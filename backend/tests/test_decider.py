"""Deterministic tests for the typed decider and tour selection.

The completions client is stubbed, so no test makes a network call.
"""

import asyncio
import math
import re
from types import SimpleNamespace

import pytest

from src.tours import selector
from src.utility.decider import (
    Decider,
    Question,
    apply_temperature,
    build_body,
    fit_temperature,
    glm_prompt,
    map_logprobs,
)


def _response(top: dict[str, float], prompt_tokens: int = 100):
    return SimpleNamespace(
        choices=[SimpleNamespace(logprobs=SimpleNamespace(top_logprobs=[top]))],
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=1),
    )


class FakeClient:
    """Stub for ``AsyncOpenAI``; ``answer(prompt)`` returns token -> prob."""

    def __init__(self, answer):
        self.answer = answer
        self.calls: list[dict] = []
        self.completions = self

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        probs = self.answer(kwargs["prompt"])
        return _response({t: math.log(p) for t, p in probs.items()})


def letters(prompt: str) -> dict[str, str]:
    """option text -> letter, as shown in a choice prompt."""
    return {m[1]: m[0] for m in re.findall(r"^([A-Z])\. (.+)$", prompt, re.M)}


def run(coro):
    return asyncio.run(coro)


# --------------------------------------------------------------------------
# Prompt format
# --------------------------------------------------------------------------


def test_glm_prompt_uses_non_thinking_chat_format():
    prompt = glm_prompt("hello")
    assert prompt == "[gMASK]<sop><|user|>\nhello<|assistant|>\n</think>"


def test_choice_prompt_letters_options_and_asks_for_letter():
    q = Question.choice("q", "Pick one.", ["red", "green", "blue"])
    body = build_body("state", q, ["green", "blue", "red"])
    assert "A. green\nB. blue\nC. red" in body
    assert body.rstrip().endswith("Answer with only the letter of the correct option.")


def test_request_parameters():
    client = FakeClient(lambda p: {"A": 0.9})
    decider = Decider(client=client, model="m", rotations=1)
    run(decider.decide("s", [Question.choice("q", "?", ["x", "y"])]))
    call = client.calls[0]
    assert call["model"] == "m"
    assert call["max_tokens"] == 1
    assert call["temperature"] == 0
    assert call["logprobs"] == 20
    assert call["prompt"].startswith("[gMASK]<sop><|user|>\n")
    assert call["prompt"].endswith("<|assistant|>\n</think>")


# --------------------------------------------------------------------------
# Logprob -> label mapping
# --------------------------------------------------------------------------


def test_map_logprobs_matches_letter_and_text_case_and_whitespace_insensitive():
    top = {
        " A": math.log(0.3),
        "a": math.log(0.1),
        " Graph Navigation ": math.log(0.2),
        "B": math.log(0.2),
        "hello": math.log(0.2),
    }
    dist, coverage = map_logprobs(top, ["graph navigation", "prompting"], True)
    assert coverage == pytest.approx(0.8)
    assert dist["graph navigation"] == pytest.approx(0.6 / 0.8)
    assert dist["prompting"] == pytest.approx(0.2 / 0.8)


def test_map_logprobs_no_match_gives_zero_coverage():
    dist, coverage = map_logprobs({"\n": 0.0}, ["yes", "no"], False)
    assert coverage == 0.0
    assert dist == {"yes": 0.0, "no": 0.0}


def test_letters_are_ignored_for_unlettered_questions():
    _, coverage = map_logprobs(
        {"A": math.log(0.5), "Yes": math.log(0.5)}, ["yes", "no"], False
    )
    assert coverage == pytest.approx(0.5)


# --------------------------------------------------------------------------
# Rotations and the three question kinds
# --------------------------------------------------------------------------


def test_choice_rotations_cover_every_position_and_cancel_position_bias():
    q = Question.choice("q", "?", ["x", "y", "z"])

    # A biased model: 50% on whatever is in slot A, plus 30% on the truth (y).
    def biased(prompt):
        shown = letters(prompt)
        probs = {"A": 0.5}
        probs[shown["y"]] = probs.get(shown["y"], 0) + 0.3
        return probs

    client = FakeClient(biased)
    decision = run(Decider(client=client, rotations=4).decide("s", [q]))["q"]

    # 3 options -> 3 distinct rotations, each option in each slot exactly once.
    assert len(client.calls) == 3
    slots = [letters(c["prompt"]) for c in client.calls]
    for option in q.options:
        assert sorted(s[option] for s in slots) == ["A", "B", "C"]

    assert decision.answer == "y"
    assert decision.distribution["x"] == pytest.approx(decision.distribution["z"])
    assert sum(decision.distribution.values()) == pytest.approx(1.0)
    assert decision.coverage == pytest.approx(0.8)


def test_yes_no_asks_both_orders():
    client = FakeClient(lambda p: {"Yes": 0.7, "No": 0.2})
    decision = run(
        Decider(client=client).decide("s", [Question.yes_no("u", "Urgent?")])
    )["u"]
    assert len(client.calls) == 2
    prompts = [c["prompt"] for c in client.calls]
    assert any("only yes or no" in p for p in prompts)
    assert any("only no or yes" in p for p in prompts)
    assert decision.answer == "yes"
    assert decision.probability == pytest.approx(0.7 / 0.9)
    assert decision.expected_score is None


def test_score_keeps_order_and_returns_expected_score():
    client = FakeClient(lambda p: {"4": 0.5, "5": 0.3, "2": 0.2})
    decision = run(
        Decider(client=client).decide("s", [Question.score("f", "Frustration?")])
    )["f"]
    assert len(client.calls) == 1
    assert "from 1 to 5" in client.calls[0]["prompt"]
    assert list(decision.distribution) == ["1", "2", "3", "4", "5"]
    assert decision.answer == "4"
    assert decision.expected_score == pytest.approx(4 * 0.5 + 5 * 0.3 + 2 * 0.2)


def test_decide_answers_every_question_and_tracks_usage():
    client = FakeClient(lambda p: {"A": 0.6, "yes": 0.6, "3": 0.6})
    decider = Decider(client=client)
    qs = [
        Question.choice("c", "?", ["a1", "a2"]),
        Question.yes_no("y", "?"),
        Question.score("s", "?"),
    ]
    out = run(decider.decide("state", qs))
    assert set(out) == {"c", "y", "s"}
    assert decider.usage.requests == 2 + 2 + 1
    assert decider.usage.prompt_tokens == 500
    assert decider.usage.completion_tokens == 5


def test_question_validation():
    with pytest.raises(ValueError):
        Question.choice("q", "?", ["only"])
    with pytest.raises(ValueError):
        Question.choice("q", "?", ["Same", " same "])
    assert Question.score("s", "?", 0, 3).options == ("0", "1", "2", "3")


# --------------------------------------------------------------------------
# Temperature
# --------------------------------------------------------------------------


def test_fit_temperature_softens_overconfident_model():
    dists = [{"a": 0.99, "b": 0.01}] * 6 + [{"a": 0.01, "b": 0.99}] * 4
    labels = ["a"] * 6 + ["a"] * 4  # wrong 40% of the time while ~99% sure
    t = fit_temperature(dists, labels)
    assert t > 1.0
    calibrated = apply_temperature({"a": 0.99, "b": 0.01}, t)
    assert calibrated["a"] < 0.99


def test_fit_temperature_sharpens_underconfident_model():
    dists = [{"a": 0.6, "b": 0.4}] * 10
    assert fit_temperature(dists, ["a"] * 10) < 1.0


def test_calibrate_stores_temperature_used_by_later_decisions():
    q = Question.choice("q", "?", ["x", "y"])

    def always_x(prompt):
        return {letters(prompt)["x"]: 0.95, letters(prompt)["y"]: 0.05}

    decider = Decider(client=FakeClient(always_x))
    t = run(decider.calibrate(q, [("s1", "x"), ("s2", "y"), ("s3", "x"), ("s4", "y")]))
    assert t > 1.0
    assert decider.temperatures["q"] == t
    after = run(decider.decide("s", [q]))["q"]
    assert after.probability < 0.95


# --------------------------------------------------------------------------
# Tour selection
# --------------------------------------------------------------------------


def _pick(option: str, p: float = 0.9):
    def answer(prompt):
        return {letters(prompt)[option]: p}

    return answer


def test_tour_question_has_every_tour_and_none_option():
    q = selector.tour_question()
    assert q.kind == "choice"
    assert q.options == ("graph navigation", "prompting", "none")
    for tour in selector.TOURS:
        assert tour.covers in q.text
    assert "Dutch or English" in q.text


@pytest.mark.parametrize(
    ("option", "tour_id"),
    [
        ("graph navigation", "graph-navigation"),
        ("prompting", "prompting"),
        ("none", None),
    ],
)
def test_select_tour_maps_answer_to_tour_id(option, tour_id):
    client = FakeClient(_pick(option))
    result = run(selector.select_tour(Decider(client=client), "Hoe navigeer ik?"))
    assert result.tour_id == tour_id
    assert result.probability == pytest.approx(1.0)
    assert set(result.distribution) == {"graph-navigation", "prompting", "none"}
    assert "Hoe navigeer ik?" in client.calls[0]["prompt"]


def test_endpoint_returns_selection(monkeypatch):
    from src.endpoints import tours as tours_endpoint

    decider = Decider(client=FakeClient(_pick("prompting", 0.8)))
    body = tours_endpoint.TourSelectRequest(question="How do I ask good questions?")
    response = run(
        tours_endpoint.select_tour_endpoint(body, user={"sub": "u"}, decider=decider)
    )
    assert response.tour_id == "prompting"
    assert response.coverage == pytest.approx(0.8)


def test_endpoint_without_api_key_is_unavailable(monkeypatch):
    from fastapi import HTTPException

    from src.endpoints import tours as tours_endpoint

    monkeypatch.delenv("NEBIUS_API_KEY", raising=False)
    monkeypatch.setattr(tours_endpoint, "_decider", None)
    with pytest.raises(HTTPException) as exc:
        tours_endpoint.get_decider()
    assert exc.value.status_code == 503
