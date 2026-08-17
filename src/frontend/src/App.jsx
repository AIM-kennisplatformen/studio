import { useState, useRef, useEffect } from "react";
import "./index.css";
import ChatWindow from "./components/chatwindow/ChatWindow.jsx";
import Graph from "./components/graph/Graph.jsx";
import { ReactFlowProvider } from "@xyflow/react";
import { fetchGraphAnswer as fetchAnswer } from "./data/graphResponse.js";
import { useAtomValue } from "jotai";
import { graphRefetchTriggerAtom } from "./lib/atoms";
import { FeedbackButton } from "./components/FeedbackButton.jsx";

const RESIZER_WIDTH = 4; // px, matches the `w-1` resizer handle
const CHAT_MIN_WIDTH = 448; // px, single source of truth for the chat pane's min-width

// Largest leftWidth (%) that still leaves the chat pane at least
// CHAT_MIN_WIDTH px, for a container of the given pixel width.
function clampLeftWidth(widthPercent, containerWidth) {
  const maxPercent =
    ((containerWidth - CHAT_MIN_WIDTH - RESIZER_WIDTH) / containerWidth) *
    100;
  return Math.min(Math.max(widthPercent, 10), Math.min(maxPercent, 90));
}

export default function App() {
  const [leftWidth, setLeftWidth] = useState(66.6);
  const containerRef = useRef(null);
  const [data, setData] = useState(null);
  const refetchTrigger = useAtomValue(graphRefetchTriggerAtom); //Read only to trigger refetch when ai signals done

  // Load graph once on mount or when center node changes for the first time
  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        const resp = await fetchAnswer();
        if (!mounted) return;
        setData(resp);
      } catch (err) {
        console.warn("Failed to load graph data", err);
      }
    })();
    return () => (mounted = false);
  }, [refetchTrigger]);

  // Re-clamp on window resize too, so shrinking the browser can't push the
  // graph/resizer/feedback-button past the chat pane's min-width either.
  useEffect(() => {
    const onResize = () => {
      if (!containerRef.current) return;
      setLeftWidth((w) => clampLeftWidth(w, containerRef.current.offsetWidth));
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const handleMouseDown = (e) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = leftWidth;

    const onMouseMove = (e) => {
      if (!containerRef.current) return;
      const containerWidth = containerRef.current.offsetWidth;
      const newWidth =
        (((startWidth / 100) * containerWidth + (e.clientX - startX)) /
          containerWidth) *
        100;
      setLeftWidth(clampLeftWidth(newWidth, containerWidth));
    };

    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  };

  return (
    <div ref={containerRef} className="flex h-screen w-screen">
      <div
        className={`h-full overflow-hidden bg-gray-100 width-[${leftWidth}%]`}>
        <ReactFlowProvider>
          <Graph data={data} width={leftWidth} />
        </ReactFlowProvider>
      </div>

      <div
        className={`pointer-events-auto absolute bottom-[120px]`}
        style={{
          left: `calc(${leftWidth}% - 86px)`,
        }}>
        <FeedbackButton />
      </div>

      <div
        className="w-1 cursor-col-resize bg-gray-400 hover:bg-gray-600"
        onMouseDown={handleMouseDown}
      />

      <div
        className="flex h-full flex-1 flex-col overflow-hidden bg-gray-50"
        style={{ minWidth: CHAT_MIN_WIDTH }}>
        <ChatWindow />
      </div>
    </div>
  );
}
