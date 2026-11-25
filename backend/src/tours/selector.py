"""Pick the onboarding tour that best fits a user's help question.

The user types a question about the ChatEP UI (in Dutch or English) while in
help mode. We ask the decider one choice question whose options are the
tours plus an explicit "none" option. The model's top answer is the result:
if it picks "none", no tour is started.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.utility.decider import Decider, Decision, Question

NO_TOUR_OPTION = "none"


@dataclass(frozen=True)
class Tour:
    id: str  # id the frontend uses to start the tour
    option: str  # short label shown to the model as a lettered option
    covers: str  # what this tour explains; goes into the question text


TOURS: tuple[Tour, ...] = (
    Tour(
        id="graph-navigation",
        option="graph navigation",
        covers=(
            "how to operate the knowledge graph in the interface: what nodes "
            "and their connections represent, clicking a node to expand it, "
            "moving between levels, and how the selected (active) node "
            "restricts which documents ChatEP uses for its answers"
        ),
    ),
    Tour(
        id="prompting",
        option="prompting",
        covers=(
            "best practices for writing questions to ChatEP: being specific, "
            "giving context, asking follow-up questions, and how to get better "
            "or more useful answers"
        ),
    ),
)


def tour_question(tours: tuple[Tour, ...] = TOURS) -> Question:
    owned = "\n".join(f"- {t.option}: {t.covers}" for t in tours)
    text = (
        "The user is using ChatEP, a chat assistant with an interactive "
        "knowledge graph, and asked the help question above. The question may "
        "be in Dutch or English. Onboarding tours only explain how to use the "
        "ChatEP interface; they never answer questions about the subject "
        "matter itself. Which onboarding tour best answers the question?\n"
        f"{owned}\n"
        f"- {NO_TOUR_OPTION}: none of the tours above fits. Choose this when "
        "the user asks about the subject matter (a definition, facts, causes, "
        "measures or policies, e.g. 'What is X?' or 'Which measures help "
        "against Y?'), even if that topic appears in the graph. Also choose "
        "this for questions about accounts, settings, chat sessions or other "
        "parts of the app that the tours do not cover."
    )
    return Question.choice("tour", text, [t.option for t in tours] + [NO_TOUR_OPTION])


@dataclass
class TourSelection:
    tour_id: str | None
    probability: float
    distribution: dict[str, float]  # keyed by tour id, "none" for the fallback
    coverage: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "tour_id": self.tour_id,
            "probability": round(self.probability, 4),
            "distribution": {k: round(v, 4) for k, v in self.distribution.items()},
            "coverage": round(self.coverage, 4),
        }


def to_selection(decision: Decision, tours: tuple[Tour, ...] = TOURS) -> TourSelection:
    by_option = {t.option: t.id for t in tours}
    dist = {
        by_option.get(o, NO_TOUR_OPTION): p for o, p in decision.distribution.items()
    }
    tour_id = by_option.get(decision.answer)  # None when the model picked "none"
    return TourSelection(tour_id, decision.probability, dist, decision.coverage)


def help_state(user_question: str) -> str:
    return f"Help question from the user:\n{user_question.strip()}"


async def select_tour(
    decider: Decider, user_question: str, tours: tuple[Tour, ...] = TOURS
) -> TourSelection:
    question = tour_question(tours)
    decisions = await decider.decide(help_state(user_question), [question])
    return to_selection(decisions[question.name], tours)
