"""Evaluate tour selection on the labeled help questions.

Compares four ways of getting a tour plus a confidence:

1. self-reported JSON confidence (the model writes {"answer", "confidence"})
2. one logprob read
3. rotated logprob reads (one per cyclic rotation of the options, averaged)
4. rotated reads with a two-fold cross-fitted temperature

Reports accuracy, AUROC of confidence for separating right from wrong answers,
ECE, log loss, the share and accuracy of decisions with confidence >= 0.9, and
cost from token usage.

Usage (from backend/, with NEBIUS_API_KEY set):
    python scripts/evaluate_tours.py [path/to/data.jsonl]
"""

from __future__ import annotations

import asyncio
import json
import math
import string
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tours.selector import TOURS, help_state, tour_question  # noqa: E402
from src.utility.decider import (  # noqa: E402
    Decider,
    Usage,
    apply_temperature,
    build_body,
    fit_temperature,
    glm_prompt,
)

DATA = ROOT / "scripts" / "data" / "tour_requests.jsonl"
THRESHOLD = 0.9
MAX_CONCURRENCY = 16
INPUT_PER_MILLION = 0.15
OUTPUT_PER_MILLION = 0.50


class LimitedClient:
    """Caps concurrent requests so a large eval does not hit rate limits."""

    def __init__(self, client: Any, limit: int):
        self._client = client
        self._sem = asyncio.Semaphore(limit)
        self.completions = self

    async def create(self, **kwargs: Any) -> Any:
        async with self._sem:
            return await self._client.completions.create(**kwargs)


@dataclass
class Result:
    name: str
    dists: list[dict[str, float]]
    usage: Usage


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------


def auroc(scores: list[float], positives: list[bool]) -> float:
    pos = [s for s, p in zip(scores, positives) if p]
    neg = [s for s, p in zip(scores, positives) if not p]
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def ece(conf: list[float], correct: list[bool], bins: int = 10) -> float:
    total, n = 0.0, len(conf)
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, c in enumerate(conf) if lo < c <= hi or (b == 0 and c == 0)]
        if idx:
            acc = sum(correct[i] for i in idx) / len(idx)
            avg = sum(conf[i] for i in idx) / len(idx)
            total += len(idx) / n * abs(acc - avg)
    return total


def metrics(dists: list[dict[str, float]], labels: list[str]) -> dict[str, float]:
    answers = [max(d, key=d.__getitem__) for d in dists]
    conf = [d[a] for d, a in zip(dists, answers)]
    correct = [a == y for a, y in zip(answers, labels)]
    high = [i for i, c in enumerate(conf) if c >= THRESHOLD]
    eps = 1e-12
    return {
        "accuracy": sum(correct) / len(correct),
        "auroc": auroc(conf, correct),
        "ece": ece(conf, correct),
        "log_loss": -sum(math.log(max(d.get(y, 0), eps)) for d, y in zip(dists, labels))
        / len(labels),
        "share_ge_0.9": len(high) / len(conf),
        "accuracy_ge_0.9": (
            sum(correct[i] for i in high) / len(high) if high else float("nan")
        ),
    }


# --------------------------------------------------------------------------
# Methods
# --------------------------------------------------------------------------


async def self_reported(
    decider: Decider, questions: list[str], options: tuple[str, ...]
) -> list[dict[str, float]]:
    """Baseline: let the model write its own answer and confidence as JSON."""
    question = tour_question()
    usage = decider.usage

    async def one(q: str) -> dict[str, float]:
        body = build_body(help_state(q), question, options).replace(
            "Answer with only the letter of the correct option.",
            'Reply with only JSON: {"answer": "<letter>", "confidence": <0 to 1>}',
        )
        response = await decider.client.completions.create(
            model=decider.model,
            prompt=glm_prompt(body),
            max_tokens=40,
            temperature=0,
        )
        usage.requests += 1
        if response.usage is not None:
            usage.prompt_tokens += response.usage.prompt_tokens or 0
            usage.completion_tokens += response.usage.completion_tokens or 0
        n = len(options)
        try:
            text = response.choices[0].text
            parsed = json.loads(text[text.index("{") : text.rindex("}") + 1])
            answer = options[
                string.ascii_uppercase.index(parsed["answer"].strip().upper())
            ]
            c = min(max(float(parsed["confidence"]), 0.0), 1.0)
        except ValueError, KeyError, IndexError, AttributeError, TypeError:
            return dict.fromkeys(options, 1 / n)  # unparseable: no information
        rest = (1 - c) / (n - 1)
        return {o: (c if o == answer else rest) for o in options}

    return list(await asyncio.gather(*(one(q) for q in questions)))


async def logprob_reads(
    decider: Decider, questions: list[str]
) -> tuple[list[dict[str, float]], float]:
    """Distributions plus mean coverage (share of mass on declared options)."""
    question = tour_question()
    decisions = await asyncio.gather(
        *(decider.ask(help_state(q), question) for q in questions)
    )
    coverage = sum(d.coverage for d in decisions) / len(decisions)
    return [d.distribution for d in decisions], coverage


def cross_fit(
    dists: list[dict[str, float]], labels: list[str]
) -> tuple[list[dict[str, float]], list[float]]:
    """Two folds: fit a temperature on one half, apply it to the other."""
    folds = [list(range(0, len(dists), 2)), list(range(1, len(dists), 2))]
    out: list[dict[str, float]] = [{} for _ in dists]
    temps = []
    for train, test in ((folds[0], folds[1]), (folds[1], folds[0])):
        t = fit_temperature([dists[i] for i in train], [labels[i] for i in train])
        temps.append(t)
        for i in test:
            out[i] = apply_temperature(dists[i], t)
    return out, temps


# --------------------------------------------------------------------------


def to_option_labels(rows: list[dict[str, str]]) -> list[str]:
    by_id = {t.id: t.option for t in TOURS}
    return [by_id.get(r["label"], "none") for r in rows]


async def main(path: Path) -> None:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    questions = [r["question"] for r in rows]
    labels = to_option_labels(rows)
    options = tour_question().options

    base = Decider.from_env()
    client = LimitedClient(base.client, MAX_CONCURRENCY)

    def fresh(rotations: int) -> Decider:
        return Decider(client=client, model=base.model, rotations=rotations)

    d_self, d_one, d_rot = fresh(1), fresh(1), fresh(4)
    self_dists, (one_dists, one_cov), (rot_dists, rot_cov) = await asyncio.gather(
        self_reported(d_self, questions, options),
        logprob_reads(d_one, questions),
        logprob_reads(d_rot, questions),
    )
    cal_dists, temps = cross_fit(rot_dists, labels)

    n_rot = len(d_rot.orders(tour_question()))
    results = [
        Result("self-reported JSON", self_dists, d_self.usage),
        Result("1 logprob read", one_dists, d_one.usage),
        Result(f"{n_rot} rotated reads", rot_dists, d_rot.usage),
        Result(f"{n_rot} rotated + cross-fit T", cal_dists, d_rot.usage),
    ]

    print(f"Model: {base.model}   examples: {len(rows)}   options: {list(options)}")
    if n_rot < 4:
        print(f"(only {n_rot} distinct rotations exist for {len(options)} options)")
    print(f"Mean coverage: 1 read {one_cov:.3f}, rotated {rot_cov:.3f}")
    print(f"Cross-fitted temperatures per fold: {temps}\n")
    header = (
        f"{'method':<28}{'acc':>7}{'AUROC':>8}{'ECE':>7}{'logloss':>9}"
        f"{'>=0.9':>7}{'acc>=0.9':>10}{'reqs':>6}{'in tok':>8}{'out tok':>8}{'cost $':>10}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        m = metrics(r.dists, labels)
        cost = r.usage.cost_usd(INPUT_PER_MILLION, OUTPUT_PER_MILLION)
        print(
            f"{r.name:<28}{m['accuracy']:>7.3f}{m['auroc']:>8.3f}{m['ece']:>7.3f}"
            f"{m['log_loss']:>9.3f}{m['share_ge_0.9']:>7.2f}{m['accuracy_ge_0.9']:>10.3f}"
            f"{r.usage.requests:>6}{r.usage.prompt_tokens:>8}{r.usage.completion_tokens:>8}"
            f"{cost:>10.5f}"
        )
    print("\n(the cross-fit row reuses the rotated reads, so it costs nothing extra)")


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]) if len(sys.argv) > 1 else DATA))
