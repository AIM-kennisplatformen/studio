/* Copied of PoC-Robert-React-Flow */
import { Handle, Position } from "@xyflow/react";
import { useRef, useLayoutEffect, useState } from "react";
import { NodeBody } from "./NodeBody";

export function BreadcrumbNode({ data }) {
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
  // const isSelected = distance === 0;
  // const isDistant = distance !== null && distance > 1;

  // Calculate scaling - 130% for selected nodes
  // const scale = isSelected ? 1.3 : 1.0;

  // Base dimensions (inner content size)
  const baseWidth = data.width || 160;

  // Wrapper dimensions match the visual size after scaling
  const wrapperWidth = baseWidth * scale;
  const wrapperHeight = contentHeight * scale;

  // Calculate styling
  // const fontWeight = isSelected ? "bold" : data.fontWeight || "normal";
  // const zIndex = isSelected ? 1000 : "auto";

  // Distant node styling - using CSS variables
  const textColor = "yellow"; //data.color || "#000";
  const background = "purple"; //data.background || "#fff";

  return (
    <div
      className="breadcrumb-node-wrapper"
      style={{
        width: wrapperWidth,
        height: wrapperHeight,
        position: "relative",
        transition: "width 300ms ease-out, height 300ms ease-out",
        zIndex,
      }}
    >
      {/* Handles on all four sides - attached to wrapper */}
      <Handle
        type="source"
        position={Position.Top}
        id="top"
        isConnectable={false}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        isConnectable={false}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        isConnectable={false}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="source"
        position={Position.Left}
        id="left"
        isConnectable={false}
        className="opacity-0 pointer-events-none"
      />

      {/* Target handles on all sides */}
      <Handle
        type="target"
        position={Position.Top}
        id="target-top"
        isConnectable={false}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="target"
        position={Position.Right}
        id="target-right"
        isConnectable={false}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="target"
        position={Position.Bottom}
        id="target-bottom"
        isConnectable={false}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="target-left"
        isConnectable={false}
        className="opacity-0 pointer-events-none"
      />

      {/* <NodeBody data={data} /> */}
      <NodeBody
        data={data}
        selected={false}
        contentRef={contentRef}
        scale={scale}
        baseWidth={baseWidth}
        textColor={textColor}
        background={background}
        fontWeight={fontWeight}
        showDragHandle={false}
      />
    </div>
  );
}
