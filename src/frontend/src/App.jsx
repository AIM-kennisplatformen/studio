import { useState, useRef, useEffect } from "react";
import "./index.css";
import Chat from "./chat.jsx";
import Graph from "./graph.jsx";
import { ReactFlowProvider } from "@xyflow/react";
import { fetchGraphAnswer as fetchAnswer } from "./data/graphResponse.js";
import { useAtom, useAtomValue } from "jotai";
import { centerNodeAtom, graphRefetchTriggerAtom } from "./data/atoms";

export default function App() {
  const [leftWidth, setLeftWidth] = useState(66.6);
  const containerRef = useRef(null);
  const [data, setData] = useState(null);
  const [centerNodeId, setCenterNodeId] = useAtom(centerNodeAtom);
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
        ((startWidth / 100) * containerWidth + (e.clientX - startX)) /
        containerWidth *
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
      <div className="h-full bg-gray-100 overflow-hidden" style={{ width: `${leftWidth}%` }}>
        <ReactFlowProvider>
          <Graph data={data} width={leftWidth} />
        </ReactFlowProvider>
      </div>

      <div
        className="w-1 bg-gray-400 cursor-col-resize hover:bg-gray-600"
        onMouseDown={handleMouseDown}
      />

      <div className="flex-1 h-full bg-gray-50 flex flex-col overflow-hidden">
        <Chat />
      </div>
    </div>
  );
}
