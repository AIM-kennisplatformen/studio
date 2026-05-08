import { useState, useRef, useEffect } from "react";
import "./index.css";
import Chat from "./chat.jsx";
import Graph from "./graph.jsx";
import { ReactFlowProvider } from "@xyflow/react";
import { fetchGraphAnswer as fetchAnswer } from "./data/graphResponse.js";
import { useAtom } from "jotai";
import { centerNodeAtom, selectedNodeScreenPositionAtom } from "./data/atoms";
import BreadcrumbOverlay from "./components/BreadcrumbsOverlay";

export default function App() {
  const [leftWidth, setLeftWidth] = useState(66.6);
  const containerRef = useRef(null);
  const [data, setData] = useState(null);
  const [centerNodeId, setCenterNodeId] = useAtom(centerNodeAtom);
  const [selectedNodePostition] = useAtom(selectedNodeScreenPositionAtom);

  const verticalNodeHeight = selectedNodePostition.y;

  // Load graph once on mount or when center node changes for the first time
  useEffect(() => {
    let mounted = true;
    if (!centerNodeId) setCenterNodeId(1);

    (async () => {
      try {
        const resp = await fetchAnswer(centerNodeId);
        if (!mounted) return;
        setData(resp);
      } catch (err) {
        console.warn("Failed to load graph data", err);
      }
    })();

    return () => (mounted = false);
  }, [centerNodeId, setCenterNodeId]);

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
  console.log(verticalNodeHeight);

  return (
    <div ref={containerRef} className="flex h-screen w-screen">
      <div
        className="h-full bg-gray-100 overflow-hidden"
        style={{ width: `${leftWidth}%` }}
      >
        <ReactFlowProvider>
          <Graph data={data} width={leftWidth} />
        </ReactFlowProvider>
      </div>

      <div
        className="w-1 bg-gray-400 cursor-col-resize hover:bg-gray-600"
        onMouseDown={handleMouseDown}
      />

      <div className="flex-1 h-full bg-gray-50 flex flex-col">
        <Chat />
      </div>

      <div
        style={{
          position: "absolute",
          top: `${verticalNodeHeight}px`,
          left: 0,
          paddingLeft: "10px",
          zIndex: 5000,
        }}
      >
        <BreadcrumbOverlay />
      </div>
    </div>
  );
}
