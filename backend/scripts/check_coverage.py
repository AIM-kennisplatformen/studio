"""Inspect what the model's first token actually is, per prompt ending.

Coverage is the share of the first token's probability mass that lands on a
declared option (a letter or option text). Low coverage means the model wants
to emit something else first (a newline, "<think>", "The", ...), so the
probabilities we read are unreliable.

Usage (from backend/, with NEBIUS_API_KEY set):
    python scripts/check_coverage.py                      # default questions
    python scripts/check_coverage.py "Hoe stel ik een goede vraag?"
    python scripts/check_coverage.py --all-endings        # compare prompt endings
    python scripts/check_coverage.py --tokens 10          # show fewer raw tokens
"""

from __future__ import annotations

import argparse
import asyncio
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tours.selector import help_state, tour_question  # noqa: E402
from src.utility.decider import (  # noqa: E402
    TOP_LOGPROBS,
    Decider,
    build_body,
    map_logprobs,
)

# The first one is what the decider uses. The others are candidates to try if
# coverage is low; the template the model was trained on decides which works.
ENDINGS = {
    "default": "<|assistant|>\n</think>",
    "default+newline": "<|assistant|>\n</think>\n",
    "empty-think": "<|assistant|>\n<think></think>",
    "empty-think+newline": "<|assistant|>\n<think></think>\n",
    "no-think": "<|assistant|>\n",
}

DEFAULT_QUESTIONS = [
    "How can I navigate through the graph?",
    "Hoe stel ik een goede vraag aan ChatEP?",
    "Wat is energiearmoede?",
]


async def read(decider: Decider, prompt: str) -> dict[str, float]:
    response = await decider.client.completions.create(
        model=decider.model,
        prompt=prompt,
        max_tokens=1,
        temperature=0,
        logprobs=TOP_LOGPROBS,
    )
    lp = response.choices[0].logprobs
    return dict(lp.top_logprobs[0]) if lp and lp.top_logprobs else {}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("questions", nargs="*", default=DEFAULT_QUESTIONS)
    parser.add_argument("--all-endings", action="store_true")
    parser.add_argument("--tokens", type=int, default=TOP_LOGPROBS)
    args = parser.parse_args()

    decider = Decider.from_env()
    question = tour_question()
    order = list(question.options)
    endings = ENDINGS if args.all_endings else {"default": ENDINGS["default"]}
    print(f"Model: {decider.model}\n")

    summary: dict[str, list[float]] = {name: [] for name in endings}
    for q in args.questions:
        body = build_body(help_state(q), question, order)
        prompts = {
            name: f"[gMASK]<sop><|user|>\n{body}{end}" for name, end in endings.items()
        }
        tops = await asyncio.gather(*(read(decider, p) for p in prompts.values()))
        print("=" * 72)
        print(f"Question: {q}")
        for name, top in zip(prompts, tops):
            dist, coverage = map_logprobs(top, order, lettered=True)
            summary[name].append(coverage)
            answer = max(dist, key=dist.__getitem__) if coverage else "-"
            print(f"\n  ending={name!r}  coverage={coverage:.3f}  answer={answer}")
            ranked = sorted(top.items(), key=lambda kv: kv[1], reverse=True)
            for token, logprob in ranked[: args.tokens]:
                print(f"    {math.exp(logprob):7.4f}  {token!r}")

    print("\n" + "=" * 72)
    print("Mean coverage per ending (higher is better, aim for > 0.9):")
    for name, covs in summary.items():
        print(f"  {name:<22} {sum(covs) / len(covs):.3f}")


if __name__ == "__main__":
    asyncio.run(main())
