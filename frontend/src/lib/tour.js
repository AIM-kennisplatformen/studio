import { driver } from "driver.js";
import "driver.js/dist/driver.css";
import { getDefaultStore } from "jotai";
import {
  messagesAtom,
  selectedNodeAtom,
  graphMoveEndTriggerAtom,
} from "./atoms";

export const TOUR_QUESTION = "How can I navigate through the graph?";
export const TOUR_MESSAGE_NAME = "tour_message";
export const TOUR_MESSAGE_ANCHOR = '[data-tour="selection-message"]';

const store = getDefaultStore();

// Node labels used in the tour (matched case-insensitively against the graph)
const TARGET_GROUPS = "Target groups";
const GREY_LITERATURE = "Grey literature";
const DOCUMENT_TYPES = [
  "Scientific literature",
  GREY_LITERATURE,
  "Project reports",
];

// Safety cap while waiting for the graph's real "settled" signal (moveend),
// in case it never fires for some reason
const GRAPH_SETTLE_TIMEOUT_MS = 1500;

let activeTour = null;
let anchorEl = null;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitFor(getter, timeout = 3000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const value = getter();
    if (value) return value;
    await sleep(50);
  }
  return null;
}

const normalize = (text) => text.trim().toLowerCase();

function findNode(label) {
  return (
    [...document.querySelectorAll(".react-flow__node")].find(
      (node) => normalize(node.textContent) === normalize(label)
    ) ?? null
  );
}

function removeAnchor() {
  anchorEl?.remove();
  anchorEl = null;
}

/** Invisible fixed box, so driver.js can highlight several nodes as one group */
function createAnchor(rect, padding = 0) {
  removeAnchor();
  anchorEl = document.createElement("div");
  Object.assign(anchorEl.style, {
    position: "fixed",
    left: `${rect.left - padding}px`,
    top: `${rect.top - padding}px`,
    width: `${rect.width + padding * 2}px`,
    height: `${rect.height + padding * 2}px`,
    pointerEvents: "none",
  });
  document.body.appendChild(anchorEl);
  return anchorEl;
}

function groupAnchor(labels) {
  const rects = labels
    .map((label) => findNode(label)?.getBoundingClientRect())
    .filter(Boolean);
  if (rects.length === 0) return null;

  const left = Math.min(...rects.map((r) => r.left));
  const top = Math.min(...rects.map((r) => r.top));
  const right = Math.max(...rects.map((r) => r.right));
  const bottom = Math.max(...rects.map((r) => r.bottom));
  return createAnchor(
    { left, top, width: right - left, height: bottom - top },
    12
  );
}

/** Tiny anchor in the graph pane, used for the un-highlighted final step */
function graphAnchor() {
  const rect = document.querySelector(".react-flow")?.getBoundingClientRect();
  if (!rect) return null;
  return createAnchor({
    left: rect.left + rect.width / 2,
    top: rect.top + rect.height * 0.35,
    width: 1,
    height: 1,
  });
}

function addTourMessage(name, value) {
  store.set(messagesAtom, (prev) => [
    { key: (prev[0]?.key || 0) + 1, name, value },
    ...prev,
  ]);
}

function removeTourMessages() {
  store.set(messagesAtom, (prev) =>
    prev.filter((m) => m.name !== TOUR_MESSAGE_NAME)
  );
}

/** Hides the highlight overlay + popover so they don't render mid-animation */
function hideDuringTransition() {
  document.body.classList.add("tour-transitioning");
}

/** Reveals the highlight overlay + popover again; call once a step is active */
function showAfterTransition() {
  document.body.classList.remove("tour-transitioning");
}

/**
 * Simulates a user click on a node through React Flow's own click handling,
 * then waits for the graph's real moveend signal (not a guessed delay)
 * before letting the caller advance to the next step.
 */
async function clickNode(label) {
  const node = await waitFor(() => findNode(label));
  if (!node) return false;

  hideDuringTransition();
  const before = store.get(graphMoveEndTriggerAtom);
  node.click();
  await waitFor(
    () => store.get(graphMoveEndTriggerAtom) !== before,
    GRAPH_SETTLE_TIMEOUT_MS
  );
  return true;
}

/** Runs an async step action, then advances (or aborts if it failed) */
function advanceAfter(action) {
  let busy = false;
  return async (_element, _step, { driver: tour }) => {
    if (busy) return;
    busy = true;
    try {
      const ok = await action();
      if (ok === false) {
        console.warn("Onboarding tour aborted: expected graph state missing");
        tour.destroy();
        return;
      }
      tour.moveNext();
    } finally {
      busy = false;
    }
  };
}

function buildSteps() {
  return [
    {
      element: () => findNode(TARGET_GROUPS),
      popover: {
        title: "Nodes",
        description:
          "Each node in the graph represents a document or category of documents. Clicking on a node expands it to show its connections. Try clicking on <b>Target groups</b>!",
        side: "bottom",
        align: "center",
        onNextClick: advanceAfter(() => clickNode(TARGET_GROUPS)),
      },
    },
    {
      element: () => groupAnchor(DOCUMENT_TYPES),
      popover: {
        title: "Connected documents",
        description:
          "There are three types of documents available that contain information about target groups.",
        side: "bottom",
        align: "center",
        onNextClick: advanceAfter(async () => {
          addTourMessage(
            TOUR_MESSAGE_NAME,
            `You've selected **${TARGET_GROUPS}**. ChatEP's answers will now be based solely on documents relevant to this topic.`
          );
          return Boolean(
            await waitFor(() => document.querySelector(TOUR_MESSAGE_ANCHOR))
          );
        }),
      },
    },
    {
      element: TOUR_MESSAGE_ANCHOR,
      popover: {
        title: "Your selection",
        description:
          "By navigating to Target groups, ChatEP's answers will be based solely on documents relevant to this topic.",
        side: "top",
        align: "center",
      },
    },
    {
      element: () => groupAnchor(DOCUMENT_TYPES),
      popover: {
        title: "Specify the source",
        description:
          "You can further specify the source by selecting one of these nodes.",
        side: "bottom",
        align: "center",
        onNextClick: advanceAfter(() => clickNode(GREY_LITERATURE)),
      },
    },
    {
      element: () => findNode(TARGET_GROUPS),
      popover: {
        title: "Moving between levels",
        description:
          "You can navigate to different levels of the graph by clicking on nodes, or by asking a question that expands your search.",
        side: "bottom",
        align: "center",
        onNextClick: advanceAfter(() => clickNode(TARGET_GROUPS)),
      },
    },
    {
      element: () => graphAnchor(),
      popover: {
        title: "Explore your sources",
        description:
          "Navigating through the graph this way allows you to explore available sources, making sure the answer you get is relevant to your specific question.",
        side: "over",
        align: "center",
        popoverClass: "tour-floating",
        doneBtnText: "Close tutorial",
      },
    },
  ];
}

/** Puts the graph back on the node the user was on before the tour */
async function restoreSelection(initialNodeId) {
  const current = store.get(selectedNodeAtom)?.id;
  if (!initialNodeId || current === initialNodeId) return;
  document
    .querySelector(`.react-flow__node[data-id="${initialNodeId}"]`)
    ?.click();
}

export function startTour() {
  if (activeTour) return;

  const initialNodeId = store.get(selectedNodeAtom)?.id;
  addTourMessage("user", TOUR_QUESTION);

  activeTour = driver({
    steps: buildSteps(),
    // driver.js's own built-in ~400ms highlight-glide/popover-fade would run
    // *after* our hide/show handling below, adding a second, uncoordinated
    // animation on top of the real "graph settled" signal. We already
    // control exactly when a step's highlight appears, so switch it off.
    animate: false,
    showProgress: true,
    progressText: "{{current}} of {{total}}",
    showButtons: ["next", "close"],
    nextBtnText: "Next",
    doneBtnText: "Done",
    allowClose: true,
    disableActiveInteraction: true,
    stagePadding: 6,
    onHighlightStarted: (_element, step) => {
      showAfterTransition();
      document.body.classList.toggle(
        "tour-no-overlay",
        step.popover?.popoverClass === "tour-floating"
      );
    },
    onDestroyed: () => {
      showAfterTransition();
      document.body.classList.remove("tour-no-overlay");
      removeAnchor();
      removeTourMessages();
      restoreSelection(initialNodeId);
      activeTour = null;
    },
  });

  activeTour.drive();
}
