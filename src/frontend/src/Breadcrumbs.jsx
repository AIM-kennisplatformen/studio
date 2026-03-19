import { MiniMap, ReactFlow } from "@xyflow/react";

export function Breadcrumbs({ breadcrumbs }) {
  const positionedNodes = breadcrumbs.map((node, index) => ({
    ...node,
    position: {
      x: 0,
      y: index * 80,
    },
  }));

  // console.log("-----------------------------");
  // breadcrumbs.forEach((breadcrumb) => {
  //   console.log(breadcrumb.data);
  // });
  // console.log("-----------------------------");

  return (
    <>
      <ReactFlow nodes={positionedNodes} />
      <MiniMap />
    </>
  );
}
