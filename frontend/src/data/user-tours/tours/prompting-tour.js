// Temporary prompting tour for the proof of concept: the texts are placeholders.
import { driver } from "driver.js";
import "driver.js/dist/driver.css";
import { getDefaultStore } from "jotai";
import { messagesAtom } from "@/lib/atoms";

const TOUR_QUESTION = "How can I write a good question?";
const CHAT_INPUT_ANCHOR = '[data-tour="chat-input"]';

const store = getDefaultStore();

let activeTour = null;

function addUserMessage(value) {
  store.set(messagesAtom, (prev) => [
    { key: (prev[0]?.key || 0) + 1, name: "user", value },
    ...prev,
  ]);
}

const inputStep = (title, description) => ({
  element: CHAT_INPUT_ANCHOR,
  popover: { title, description, side: "top", align: "center" },
});

const STEPS = [
  inputStep(
    "Asking questions",
    "Type your question here. The way you phrase it affects how useful the answer is."
  ),
  inputStep(
    "Be specific",
    "Instead of <i>“Tell me about energy”</i>, try <i>“Which measures help households reduce energy costs?”</i>"
  ),
  inputStep(
    "Give context",
    "Mention who you are asking for and what you need, for example: <i>“I advise a municipality. Give me a short overview of…”</i>"
  ),
  inputStep(
    "Ask follow-up questions",
    "Not quite what you needed? Ask for more detail, an example or a shorter summary."
  ),
];

export function startTour(question = TOUR_QUESTION) {
  if (activeTour) return;

  addUserMessage(question);

  activeTour = driver({
    steps: STEPS,
    showProgress: true,
    progressText: "{{current}} of {{total}}",
    showButtons: ["next", "close"],
    nextBtnText: "Next",
    doneBtnText: "Close tutorial",
    allowClose: true,
    disableActiveInteraction: true,
    stagePadding: 6,
    onDestroyed: () => {
      activeTour = null;
    },
  });

  activeTour.drive();
}
