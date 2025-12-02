import React from "react";

export const SolidEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  style = {},
  markerEnd,
}) => {
  return (
    <path
      id={id}
      d={`M${sourceX},${sourceY} L${targetX},${targetY}`}
      stroke="#000"          // black line
      strokeWidth={4}        // thickness
      fill="none"
      markerEnd={markerEnd}  // optional arrowhead
      style={style}          // allow inline overrides if needed
    />
  );
};