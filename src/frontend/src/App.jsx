import { useState, useRef, useEffect } from "react";
import "./index.css";
import Chat from "./chat.jsx";
import Graph from "./graph.jsx";
import { ReactFlowProvider } from "@xyflow/react";
import { fetchGraphAnswer as fetchAnswer } from "./data/graphResponse.js";
import { useAtom, useAtomValue } from "jotai";
import { graphRefetchTriggerAtom, selectedNodeVerticalPositionAtom } from "./data/atoms";
import BreadcrumbOverlay from "./components/BreadcrumbsOverlay";
import { FeedbackButton } from "./components/FeedbackButton.jsx";

export default function App() {
  const [leftWidth, setLeftWidth] = useState(66.6);
  const containerRef = useRef(null);
  const [data, setData] = useState(null);
  const [selectedNodeVerticalPosition] = useAtom(
    selectedNodeVerticalPositionAtom
  );

  //const [refetchTrigger, setRefetchTrigger] = useAtom(graphRefetchTriggerAtom); //Read/write if we want to trigger refetch from here, but currently only chatbot triggers refetch, so read only is enough
  const refetchTrigger = useAtomValue(graphRefetchTriggerAtom); //Read only to trigger refetch when chatbot signals done

  // Load graph once on mount or when center node changes for the first time
  useEffect(() => {
    let mounted = true;
    //if (!centerNodeId) setCenterNodeId(1);

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
      if (newWidth > 10 && newWidth < 90) setLeftWidth(newWidth);
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
        className="h-full overflow-hidden bg-gray-100"
        style={{ width: `${leftWidth}%` }}>
        <ReactFlowProvider>
          <Graph data={data} />
        </ReactFlowProvider>
      </div>

      <div
        className="pointer-events-auto absolute z-50"
        style={{
          left: `calc(${leftWidth}% - 86px)`,
          bottom: "120px",
        }}>
        <FeedbackButton />
      </div>

      <div
        className="w-1 cursor-col-resize bg-gray-400 hover:bg-gray-600"
        onMouseDown={handleMouseDown}
      />

      <div className="flex h-full flex-1 flex-col overflow-hidden bg-gray-50">
        <Chat />
      </div>

      <div
        className="flex flex-col justify-end"
        style={{
          position: "absolute",
          top: 0,
          height: selectedNodeVerticalPosition,
          left: 0,
          zIndex: 5000,
          paddingLeft: "10px",
          width: "auto",
        }}
      >
        <div>
          <BreadcrumbOverlay />
        </div>
      </div>
    </div>
  );
}
