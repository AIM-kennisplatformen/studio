export function NodeBody({
  data,
  selected,
  contentRef,
  scale,
  baseWidth,
  textColor,
  background,
  fontWeight,
  showDragHandle,
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
      <div className="flex h-full">
        {showDragHandle ? (
          <div
            className="group/handle flex items-center justify-center cursor-move hover:brightness-[0.85] transition-[filter] duration-200 w-6 shrink-0"
            style={{
              background,
              borderTopLeftRadius: borderRadius,
              borderBottomLeftRadius: borderRadius,
            }}
          >
            <div className="flex flex-col gap-0.5">
              <div className="w-[3px] h-[3px] bg-black/30 rounded-full transition-[width] duration-500 ease-in-out group-hover/handle:w-[15px]" />
              <div className="w-[3px] h-[3px] bg-black/30 rounded-full transition-[width] duration-500 ease-in-out group-hover/handle:w-[15px]" />
              <div className="w-[3px] h-[3px] bg-black/30 rounded-full transition-[width] duration-500 ease-in-out group-hover/handle:w-[15px]" />
            </div>
          </div>
        ) : null}

        <div
          className="nodrag text-left flex-1 cursor-default"
          style={{
            padding: data.padding || "10px",
            background,
            borderTopLeftRadius: showDragHandle ? undefined : borderRadius,
            borderBottomLeftRadius: showDragHandle ? undefined : borderRadius,
            borderTopRightRadius: borderRadius,
            borderBottomRightRadius: borderRadius,
          }}
        >
          {data.label}
        </div>
      </div>
    </div>
  );
}
