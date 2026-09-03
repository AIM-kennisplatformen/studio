import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  getSmoothStepPath,
  getStraightPath,
} from "@xyflow/react"; // of '@xyflow/react'

const getStepPath = (params) =>
  getSmoothStepPath({ ...params, borderRadius: 0 });

const pathGenerators = {
  straight: getStraightPath,
  step: getStepPath,
  smoothstep: getSmoothStepPath,
  bezier: getBezierPath,
};

export const SolidEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  label,
  labelStyle,
  labelBgStyle,
  data,
}) => {
  // Selecteer de gewenste path-generator (default is 'smoothstep')
  const pathType = data?.pathType || "smoothstep";
  const getPath = pathGenerators[pathType] || getSmoothStepPath;

  const [edgePath, labelX, labelY] = getPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        className="custom-solid-edge"
        style={{
          ...style,
          stroke: "var(--primary)",
          strokeWidth: 2,
          strokeDasharray: "none",
        }}
        markerEnd={markerEnd}
      />

      {label && (
        <EdgeLabelRenderer>
          <div
            className="nodrag nopan"
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              fontSize: "12px",
              pointerEvents: "all",
              ...labelStyle,
            }}>
            <div
              style={{
                background: "white",
                padding: "2px 4px",
                borderRadius: "3px",
                ...labelBgStyle,
              }}>
              {label}
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};
