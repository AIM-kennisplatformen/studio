/* Copied of PoC-Robert-React-Flow */
import { Handle, Position } from "@xyflow/react";
import { useRef, useLayoutEffect, useState } from "react";

export function CustomNode({ data, isConnectable, selected }) {
  const nodeBackground = data.background || "#fff";
  const distance = data.distance ?? null;
  const contentRef = useRef(null);
  const [contentHeight, setContentHeight] = useState(80); // Default height

  // Measure content height on mount and when data changes
  useLayoutEffect(() => {
    if (contentRef.current) {
      const height = contentRef.current.offsetHeight;
      setContentHeight(height);
    }
  }, [data.label]); // Re-measure if label changes

  // Determine visual state based on distance
  const isSelected = distance === 0;
  const isDistant = distance !== null && distance > 1;

  // Calculate scaling - 130% for selected nodes
  const scale = isSelected ? 1.3 : 1.0;

  // Base dimensions (inner content size)
  const baseWidth = data.width || 160;

  // Wrapper dimensions match the visual size after scaling
  const wrapperWidth = baseWidth * scale;
  const wrapperHeight = contentHeight * scale;

  // Calculate styling
  const fontWeight = isSelected ? "bold" : data.fontWeight || "normal";
  const zIndex = isSelected ? 1000 : "auto";

  // Distant node styling - using CSS variables
  const textColor = isDistant
    ? "var(--distant-node-text-color)"
    : data.color || "#000";
  const background = isDistant
    ? "var(--distant-node-background-color)"
    : nodeBackground;

  return (
    <div
      className="custom-node-wrapper"
      style={{
        width: wrapperWidth,
        height: wrapperHeight,
        position: "relative",
        transition: "width 300ms ease-out, height 300ms ease-out",
        zIndex,
      }}>
      {/* Handles on all four sides - attached to wrapper */}
      <Handle
        type="source"
        position={Position.Top}
        id="top"
        isConnectable={isConnectable}
        className="pointer-events-none opacity-0"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        isConnectable={isConnectable}
        className="pointer-events-none opacity-0"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        isConnectable={isConnectable}
        className="pointer-events-none opacity-0"
      />
      <Handle
        type="source"
        position={Position.Left}
        id="left"
        isConnectable={isConnectable}
        className="pointer-events-none opacity-0"
      />

      {/* Target handles on all sides */}
      <Handle
        type="target"
        position={Position.Top}
        id="target-top"
        isConnectable={isConnectable}
        className="pointer-events-none opacity-0"
      />
      <Handle
        type="target"
        position={Position.Right}
        id="target-right"
        isConnectable={isConnectable}
        className="pointer-events-none opacity-0"
      />
      <Handle
        type="target"
        position={Position.Bottom}
        id="target-bottom"
        isConnectable={isConnectable}
        className="pointer-events-none opacity-0"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="target-left"
        isConnectable={isConnectable}
        className="pointer-events-none opacity-0"
      />

      {/* Inner content div - centered and scaled */}
      <div
        ref={contentRef}
        className={`custom-node ${data.isFocused ? "focussed-node" : ""}`}
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: `translate(-50%, -50%) scale(${scale})`,
          transformOrigin: "center center",
          width: baseWidth,
          fontWeight,
          cursor: "default",
        }}>
        {/* Flexbox container with content */}
        <div className="nodrag flex-1 cursor-default text-left">
          {data.label}
        </div>
      </div>
    </div>
  );
}
