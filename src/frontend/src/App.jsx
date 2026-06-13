import { useState, useRef, useEffect } from "react";
import "./index.css";
import Chat from "./chat.jsx";
import Graph from "./graph.jsx";
import { ReactFlowProvider } from "@xyflow/react";
import { fetchGraphAnswer as fetchAnswer } from "./data/graphResponse.js";
import { useAtom, useAtomValue } from "jotai";
import {
  graphRefetchTriggerAtom,
  selectedNodeVerticalPositionAtom,
  selectedNodeScreenCenterAtom,
  lastCrumbScreenCenterAtom,
} from "./data/atoms";
import BreadcrumbOverlay from "./components/BreadcrumbsOverlay";
import { FeedbackButton } from "./components/FeedbackButton.jsx";

// Clip the connector's node-side endpoint to the node's rectangle border, so
// the line stops at the edge of the node instead of crossing over it and its
// text. `node` is { x, y, hw, hh } (center + half-width/half-height in screen
// coords); `from` is the point the line comes from (the breadcrumb center).
// Returns the point on the node's border along the line from center → from.
function clipToNodeEdge(node, from) {
  const dx = from.x - node.x;
  const dy = from.y - node.y;
  if (dx === 0 && dy === 0) return { x: node.x, y: node.y };
  const hw = node.hw ?? 0;
  const hh = node.hh ?? 0;
  // Scale the direction vector so it just reaches the nearest border. For each
  // axis the border is hit at |half / delta|; the smaller factor wins.
  const tx = dx === 0 ? Infinity : hw / Math.abs(dx);
  const ty = dy === 0 ? Infinity : hh / Math.abs(dy);
  const t = Math.min(tx, ty);
  return { x: node.x + dx * t, y: node.y + dy * t };
}

export default function App() {
  const [leftWidth, setLeftWidth] = useState(66.6);
  const containerRef = useRef(null);
  const [data, setData] = useState(null);
  const [selectedNodeVerticalPosition] = useAtom(
    selectedNodeVerticalPositionAtom
  );
  // Debug markers
  const nodeCenter = useAtomValue(selectedNodeScreenCenterAtom);
  const crumbCenter = useAtomValue(lastCrumbScreenCenterAtom);

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
        }}>
        <div>
          <BreadcrumbOverlay />
        </div>
      </div>

      {/* Connector: line from the last breadcrumb to the selected node. The
          node-side endpoint is clipped to the node's rectangle border so the
          line stops at the edge instead of crossing over the node and its text. */}
      {nodeCenter && crumbCenter && (
        <svg
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            pointerEvents: "none",
            zIndex: 1,
          }}>
          {(() => {
            const nodeEdge = clipToNodeEdge(nodeCenter, crumbCenter);
            return (
              <line
                x1={nodeEdge.x}
                y1={nodeEdge.y}
                x2={crumbCenter.x}
                y2={crumbCenter.y}
                stroke="green"
                strokeWidth="2"
                strokeDasharray="4 4"
              />
            );
          })()}
        </svg>
      )}
    </div>
  );
}
