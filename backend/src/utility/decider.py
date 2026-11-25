"""Typed decision model on top of a raw completions endpoint.

Unstructured state goes in, typed answers with probabilities come out. The
model never generates free text: every question is asked with
``max_tokens=1`` and the answer is read from the top logprobs of that single
token, so there is no output parsing.

Choice and yes/no questions are asked once per cyclic rotation of the option
order (in parallel). Each rotation is renormalized and the rotations are
averaged, which cancels the model's position bias. Score questions keep their
options in order and also report the expected score.
"""

from __future__ import annotations

import asyncio
import math
import os
import string
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
DEFAULT_MODEL = "zai-org/GLM-5.3-Flash"
DEFAULT_ROTATIONS = 4
TOP_LOGPROBS = 20
TEMPERATURE_GRID: tuple[float, ...] = tuple(
    round(0.1 * i, 2) for i in range(1, 51)
)  # 0.1 .. 5.0

QuestionKind = Literal["choice", "yes_no", "score"]


def _norm(text: str) -> str:
    """Case- and whitespace-insensitive key."""
    return "".join(text.split()).lower()


@dataclass(frozen=True)
class Question:
    """A typed question. Build one with ``choice``, ``yes_no`` or ``score``."""

    name: str
    text: str
    kind: QuestionKind
    options: tuple[str, ...]

    @classmethod
    def choice(cls, name: str, text: str, options: Sequence[str]) -> Question:
        opts = tuple(options)
        if len(opts) < 2:
            raise ValueError("a choice question needs at least two options")
        if len(opts) > len(string.ascii_uppercase):
            raise ValueError("too many options to letter")
        if len({_norm(o) for o in opts}) != len(opts):
            raise ValueError("choice options must be distinct")
        return cls(name, text, "choice", opts)

    @classmethod
    def yes_no(cls, name: str, text: str) -> Question:
        return cls(name, text, "yes_no", ("yes", "no"))

    @classmethod
    def score(cls, name: str, text: str, low: int = 1, high: int = 5) -> Question:
        if high <= low:
            raise ValueError("score rubric needs high > low")
        return cls(name, text, "score", tuple(str(i) for i in range(low, high + 1)))


@dataclass
class Decision:
    answer: str
    probability: float
    distribution: dict[str, float]
    coverage: float
    expected_score: float | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "answer": self.answer,
            "probability": round(self.probability, 4),
            "distribution": {k: round(v, 4) for k, v in self.distribution.items()},
            "coverage": round(self.coverage, 4),
        }
        if self.expected_score is not None:
            out["expected_score"] = round(self.expected_score, 4)
        return out


@dataclass
class Usage:
    requests: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0

    def cost_usd(
        self, input_per_million: float = 0.15, output_per_million: float = 0.50
    ) -> float:
        return (
            self.prompt_tokens * input_per_million
            + self.completion_tokens * output_per_million
        ) / 1_000_000


# --------------------------------------------------------------------------
# Prompting
# --------------------------------------------------------------------------


def glm_prompt(body: str) -> str:
    """Wrap a user turn in GLM's non-thinking chat format.

    The assistant turn opens with an already-closed think block, so the very
    next token is the answer key.
    """
    return f"[gMASK]<sop><|user|>\n{body}<|assistant|>\n</think>"


def rotate(options: Sequence[str], k: int) -> list[str]:
    k %= len(options)
    return list(options[k:]) + list(options[:k])


def build_body(state: str, question: Question, order: Sequence[str]) -> str:
    lines = ["Context:", state.strip(), "", f"Question: {question.text.strip()}"]
    if question.kind == "choice":
        lines.append("")
        for letter, option in zip(string.ascii_uppercase, order):
            lines.append(f"{letter}. {option}")
        lines.append("")
        lines.append("Answer with only the letter of the correct option.")
    elif question.kind == "yes_no":
        lines.append(f"Answer with only {order[0]} or {order[1]}.")
    else:
        lines.append(
            f"Answer with only a single integer from {order[0]} to {order[-1]}."
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Logprob mapping
# --------------------------------------------------------------------------


def map_logprobs(
    top_logprobs: dict[str, float], order: Sequence[str], lettered: bool
) -> tuple[dict[str, float], float]:
    """Map top-token logprobs onto the declared options.

    A token counts for an option when it equals the option's letter (for
    lettered prompts) or the option text, ignoring case and whitespace.
    Returns the renormalized distribution over ``order`` and the coverage, i.e.
    the share of probability mass that landed on a declared option.
    """
    keys: dict[str, str] = {}
    for i, option in enumerate(order):
        keys.setdefault(_norm(option), option)
        if lettered:
            keys.setdefault(_norm(string.ascii_uppercase[i]), option)

    mass = dict.fromkeys(order, 0.0)
    for token, logprob in top_logprobs.items():
        option = keys.get(_norm(token))
        if option is not None and logprob is not None:
            mass[option] += math.exp(logprob)

    coverage = min(sum(mass.values()), 1.0)
    total = sum(mass.values())
    if total <= 0:
        return dict.fromkeys(order, 0.0), 0.0
    return {o: p / total for o, p in mass.items()}, coverage


def apply_temperature(dist: dict[str, float], temperature: float) -> dict[str, float]:
    if temperature == 1.0:
        return dict(dist)
    floor = 1e-12
    scaled = {k: math.log(max(p, floor)) / temperature for k, p in dist.items()}
    top = max(scaled.values())
    exp = {k: math.exp(v - top) for k, v in scaled.items()}
    total = sum(exp.values())
    return {k: v / total for k, v in exp.items()}


def log_loss(dists: Sequence[dict[str, float]], labels: Sequence[str]) -> float:
    eps = 1e-12
    return -sum(math.log(max(d.get(y, 0.0), eps)) for d, y in zip(dists, labels)) / max(
        len(labels), 1
    )


def fit_temperature(
    dists: Sequence[dict[str, float]],
    labels: Sequence[str],
    grid: Iterable[float] = TEMPERATURE_GRID,
) -> float:
    """Pick the temperature from ``grid`` that minimizes log loss."""
    best_t, best_loss = 1.0, log_loss(dists, labels)
    for t in grid:
        loss = log_loss([apply_temperature(d, t) for d in dists], labels)
        if loss < best_loss - 1e-12:
            best_t, best_loss = t, loss
    return best_t


# --------------------------------------------------------------------------
# Decider
# --------------------------------------------------------------------------


def _top_logprobs(response: Any) -> dict[str, float]:
    logprobs = response.choices[0].logprobs
    if logprobs is None or not logprobs.top_logprobs:
        return {}
    return dict(logprobs.top_logprobs[0] or {})


@dataclass
class Decider:
    """Answers typed questions about unstructured state.

    ``client`` is an ``openai.AsyncOpenAI`` (or anything exposing an async
    ``completions.create``).
    """

    client: Any
    model: str = DEFAULT_MODEL
    rotations: int = DEFAULT_ROTATIONS
    temperatures: dict[str, float] = field(default_factory=dict)
    usage: Usage = field(default_factory=Usage)

    @classmethod
    def from_env(cls, **kwargs: Any) -> Decider:
        """Build a decider from ``NEBIUS_*`` environment variables."""
        from openai import AsyncOpenAI

        api_key = os.getenv("NEBIUS_API_KEY")
        if not api_key:
            raise RuntimeError("NEBIUS_API_KEY is not set")
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=os.getenv("NEBIUS_BASE_URL") or DEFAULT_BASE_URL,
        )
        return cls(
            client=client, model=os.getenv("NEBIUS_MODEL") or DEFAULT_MODEL, **kwargs
        )

    def orders(self, question: Question) -> list[list[str]]:
        if question.kind == "score":
            return [list(question.options)]
        n = min(max(self.rotations, 1), len(question.options))
        return [rotate(question.options, k) for k in range(n)]

    async def _read(self, prompt: str) -> dict[str, float]:
        response = await self.client.completions.create(
            model=self.model,
            prompt=prompt,
            max_tokens=1,
            temperature=0,
            logprobs=TOP_LOGPROBS,
        )
        self.usage.requests += 1
        usage = getattr(response, "usage", None)
        if usage is not None:
            self.usage.prompt_tokens += usage.prompt_tokens or 0
            self.usage.completion_tokens += usage.completion_tokens or 0
        return _top_logprobs(response)

    async def ask(self, state: str, question: Question) -> Decision:
        """Uncalibrated-then-calibrated answer to one question."""
        orders = self.orders(question)
        reads = await asyncio.gather(
            *(self._read(glm_prompt(build_body(state, question, o))) for o in orders)
        )
        lettered = question.kind == "choice"
        mapped = [map_logprobs(r, o, lettered) for r, o in zip(reads, orders)]

        covered = [d for d, c in mapped if c > 0]
        coverage = sum(c for _, c in mapped) / len(mapped)
        if covered:
            dist = {
                o: sum(d[o] for d in covered) / len(covered) for o in question.options
            }
        else:
            dist = {o: 1 / len(question.options) for o in question.options}

        dist = apply_temperature(dist, self.temperatures.get(question.name, 1.0))
        answer = max(question.options, key=lambda o: dist[o])
        expected = (
            sum(int(o) * p for o, p in dist.items())
            if question.kind == "score"
            else None
        )
        return Decision(answer, dist[answer], dist, coverage, expected)

    async def decide(
        self, state: str, questions: Sequence[Question]
    ) -> dict[str, Decision]:
        """Answer every question in parallel."""
        start = time.perf_counter()
        results = await asyncio.gather(*(self.ask(state, q) for q in questions))
        self.usage.latency_s += time.perf_counter() - start
        return {q.name: r for q, r in zip(questions, results)}

    async def calibrate(
        self,
        question: Question,
        examples: Sequence[tuple[str, str]],
        grid: Iterable[float] = TEMPERATURE_GRID,
    ) -> float:
        """Fit and store one temperature for ``question`` on labeled examples.

        ``examples`` are ``(state, correct_option)`` pairs.
        """
        previous = self.temperatures.pop(question.name, None)
        try:
            decisions = await asyncio.gather(
                *(self.ask(state, question) for state, _ in examples)
            )
        except BaseException:
            if previous is not None:
                self.temperatures[question.name] = previous
            raise
        t = fit_temperature(
            [d.distribution for d in decisions], [y for _, y in examples], grid
        )
        self.temperatures[question.name] = t
        return t
