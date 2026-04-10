export function NodeBody({
  data,
  selected,
  contentRef,
  scale,
  baseWidth,
  textColor,
  background,
  fontWeight,
}) {
  const borderRadius = data.borderRadius || "3px";

  return (
    <div
      ref={contentRef}
      className="custom-node"
      style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: `translate(-50%, -50%) scale(${scale})`,
        transformOrigin: "center center",
        width: baseWidth,
        color: textColor,
        border: selected
          ? "3px solid #1a73e8"
          : data.border || "1px solid #000",
        borderRadius,
        fontSize: data.fontSize || "12px",
        fontWeight,
        whiteSpace: data.whiteSpace || "normal",
        boxShadow: selected
          ? "0 0 0 2px rgba(26, 115, 232, 0.2), 0 4px 12px rgba(0, 0, 0, 0.15)"
          : data.boxShadow || "none",
        transition:
          "color 300ms ease-out, font-weight 300ms ease-out, transform 300ms ease-out",
      }}
    >
      {/* Flexbox container with content */}
      <div
        className="nodrag text-left flex-1 cursor-default"
        style={{
          padding: data.padding || "10px",
          background,
          borderRadius: data.borderRadius || "3px",
        }}
      >
        {data.label}
      </div>
    </div>
  );
}
