import { applyNodeChanges, MiniMap, ReactFlow } from "@xyflow/react";

export function Breadcrumbs({ breadcrumbs }) {
  const positionedNodes = breadcrumbs.map((node, index) => ({
    ...node,
    position: {
      x: 0,
      y: index * 80,
    },
  }));

  return (
    <>
      <ReactFlow nodes={positionedNodes} />
      <MiniMap />
    </>
  );
}
