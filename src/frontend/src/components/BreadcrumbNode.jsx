/* Copied of PoC-Robert-React-Flow */
import { Handle, Position } from "@xyflow/react";
import { useRef, useLayoutEffect, useState } from "react";
import { NodeBody } from "./NodeBody";

export function BreadcrumbNode({ data }) {
  const contentRef = useRef(null);
  const [contentHeight, setContentHeight] = useState(80); // Default height
  const nodeBackground = data.background || "#fff";

  // Measure content height on mount and when data changes
  useLayoutEffect(() => {
    if (contentRef.current) {
      const height = contentRef.current.offsetHeight;
      setContentHeight((currentHeight) =>
        currentHeight === height ? currentHeight : height
      );
    }
  }, [data.label]); // Re-measure if label changes

  const scale = 1;
  const baseWidth = data.width || 160;

  const wrapperWidth = baseWidth * scale;
  const wrapperHeight = contentHeight * scale;

  const fontWeight = data.fontWeight || "normal";
  const zIndex = "auto";
  const textColor = "white"; //data.color || "#000";
  const background = "blue"; //nodeBackground;

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
