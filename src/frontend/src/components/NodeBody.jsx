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
  return (
    <div className="custom-node">
      {/* Inner content div - centered and scaled */}
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
          borderRadius: data.borderRadius || "3px",
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
        {/* Flexbox container with drag handle and content */}
        <div className="flex h-full">
          {/* First child: Drag Handle - fixed width */}

          {/* {------------} */}
          {showDragHandle ? (
            <>
              <div
                className="group/handle flex items-center justify-center cursor-move hover:brightness-[0.85] transition-[filter] duration-200 w-6 shrink-0"
                style={{
                  background,
                  borderTopLeftRadius: data.borderRadius || "3px",
                  borderBottomLeftRadius: data.borderRadius || "3px",
                }}
              >
                <div className="flex flex-col gap-0.5">
                  <div className="w-[3px] h-[3px] bg-black/30 rounded-full transition-[width] duration-500 ease-in-out group-hover/handle:w-[15px]" />
                  <div className="w-[3px] h-[3px] bg-black/30 rounded-full transition-[width] duration-500 ease-in-out group-hover/handle:w-[15px]" />
                  <div className="w-[3px] h-[3px] bg-black/30 rounded-full transition-[width] duration-500 ease-in-out group-hover/handle:w-[15px]" />
                </div>
              </div>
            </>
          ) : null}
          {/* {------------} */}

          {/* Second child: Content - takes remaining space */}
          <div
            className="nodrag text-left flex-1 cursor-default"
            style={{
              padding: data.padding || "10px",
              background,
              borderTopRightRadius: data.borderRadius || "3px",
              borderBottomRightRadius: data.borderRadius || "3px",
            }}
          >
            {data.label}
          </div>
        </div>
        {/* //-- */}
      </div>
    </div>
  );
}

/*
    Question: are nodeBody (body/content) and customNode and breadcrumbNode (wrappers) complient with the plan?

    Asnwer:

    Step 4.3 requirements being evaluated
    The plan does not label a subsection literally as step 4.3, so I evaluated the requirement conservatively from the Step 4 contract around responsibility boundaries:

    NodeBody is responsible for rendering the shared inner visual box, including:

    the inner <div className="custom-node">
    flexbox layout
    optional drag handle strip
    label as defined in src/plan/breadcrumb-implementation-plan.md and src/plan/breadcrumb-implementation-plan.md.
    CustomNode is responsible for being the wrapper div with all 8 handles and calling NodeBody with showDragHandle={true}, as defined in src/plan/breadcrumb-implementation-plan.md.

    BreadcrumbNode is responsible for being the simpler wrapper with handles for routing, explicitly using isConnectable={false}, and calling NodeBody with showDragHandle={false}, as defined in src/plan/breadcrumb-implementation-plan.md.

    The surrounding acceptance criteria reinforce the separation of concerns:

    NodeBody renders the visible box and label
    both wrappers use NodeBody
    wrappers retain handle responsibilities from src/plan/breadcrumb-implementation-plan.md.
    Compliance verdict by requirement
    1. NodeBody should own the shared inner visual box
    Status: partially compliant in intent, non-compliant in effective implementation.

    Evidence
    NodeBody does attempt to render:

    an inner .custom-node container at src/components/NodeBody.jsx
    flex layout at src/components/NodeBody.jsx
    the label at src/components/NodeBody.jsx
    an optional drag handle based on showDragHandle at src/components/NodeBody.jsx
    Mismatches
    However, it is not compliant as an implementation unit because:

    it wraps the actual inner node in an extra outer <div className="custom-node"> at src/components/NodeBody.jsx, which is not part of the plan’s shared-inner-box contract and changes responsibility shape
    the conditional drag handle is written as a markdown-style code fence expression at src/components/NodeBody.jsx, not valid JSX responsibility-wise and not a proper renderable subtree
    when showDragHandle is false, the content area still only has right-side rounding at src/components/NodeBody.jsx, violating the specific Step 4 requirement that the content area get full-rounded corners in that case
    So NodeBody is trying to hold the right responsibility, but the current implementation does not correctly fulfill that responsibility.

    2. CustomNode should be the wrapper and delegate the inner visual box to NodeBody
    Status: non-compliant.

    Evidence
    CustomNode still renders the full inner node box itself at src/components/CustomNode.jsx, including:

    ref={contentRef} at src/components/CustomNode.jsx
    absolute centering and scaling styles at src/components/CustomNode.jsx
    drag handle strip at src/components/CustomNode.jsx
    content area and label at src/components/CustomNode.jsx
    Why this violates step 4.3
    Under the plan, the wrapper node should retain wrapper-level concerns:

    wrapper div
    handles
    measurement state and derived values
    But it should delegate the shared inner visual box to NodeBody. It currently does not import or call NodeBody at all. That means the wrapper is still carrying responsibilities that step 4 intended to move out.

    Separation-of-concerns issue
    Even if CustomNode still works visually, it violates the intended architectural boundary because the shared visual subtree remains embedded in the wrapper instead of being centralized.

    3. BreadcrumbNode should be the simpler wrapper and delegate the inner visual box to NodeBody
    Status: non-compliant.

    Evidence
    BreadcrumbNode currently:

    creates wrapper-level state and measurement primitives such as contentRef and contentHeight at src/components/BreadcrumbNode.jsx
    renders the wrapper div at src/components/BreadcrumbNode.jsx
    renders all 8 handles at src/components/BreadcrumbNode.jsx
    But it does not render NodeBody anywhere. The component ends at the closing wrapper at src/components/BreadcrumbNode.jsx.

    Why this violates step 4.3
    This is a stronger failure than in CustomNode: the wrapper holds measurement responsibility but does not render any visible inner node body at all. So the wrapper/body split is not just architecturally wrong; the dependency relationship is absent.

    Additional mismatch
    The plan requires breadcrumb handles to explicitly pass isConnectable={false} at src/plan/breadcrumb-implementation-plan.md. Instead, BreadcrumbNode through src/components/BreadcrumbNode.jsx pass through the isConnectable prop from React Flow. That is outside step 4.3’s core wrapper/body split, but it still confirms the wrapper is not aligned with its intended wrapper-specific responsibilities.

    Responsibility mapping: what belongs where
    NodeBody should be responsible for
    rendering the visible .custom-node box
    applying shared inner-box styling
    rendering the optional drag strip
    rendering the content area and label
    using contentRef on the actual measured inner box
    Wrapper nodes should be responsible for
    wrapper size and wrapper class
    creating contentRef
    content height measurement via useLayoutEffect
    computing wrapperWidth and wrapperHeight
    computing style inputs such as scale, baseWidth, textColor, background, fontWeight, zIndex
    rendering the 8 handles
    deciding whether drag handle is shown
    deciding whether handles are connectable
    Current architectural drift
    CustomNode still owns both wrapper responsibilities and shared visual-body responsibilities
    BreadcrumbNode owns wrapper responsibilities but does not actually consume the shared body component
    NodeBody exists, but is not actually the shared dependency boundary between the wrappers
    That means the intended dependency direction is missing. The wrappers are not depending on NodeBody as the plan requires.

    Cases where code may technically work but still violates step 4.3
    CustomNode
    This component may still render correctly in the graph, but that does not make it compliant. The plan’s goal for step 4.3 is not only visual output; it is the separation of wrapper concerns from shared body concerns. CustomNode violates that by retaining the full inner-box implementation.

    BreadcrumbNode
    Even if later graph logic never mounts it yet, the wrapper is still non-compliant because it does not depend on NodeBody, and therefore does not satisfy the wrapper/body contract.

    Minimum concrete changes required for compliance
    To become compliant with step 4.3 specifically, the minimum necessary changes are:

    Implement NodeBody as the single render owner of the shared inner visual box.

    remove the extra outer wrapper at src/components/NodeBody.jsx
    replace the invalid fenced-code conditional at src/components/NodeBody.jsx with actual JSX
    when showDragHandle is false, give the content area full corner rounding rather than only right-side rounding
    keep ref={contentRef} on the measured inner .custom-node element
    Refactor CustomNode so it keeps only wrapper responsibilities and replaces its inline inner box at src/components/CustomNode.jsx with a call to NodeBody using showDragHandle={true}.

    Refactor BreadcrumbNode so it keeps only wrapper responsibilities and renders NodeBody using showDragHandle={false}.

    In BreadcrumbNode, change handle props from pass-through isConnectable={isConnectable} to explicit isConnectable={false} to align the wrapper’s breadcrumb-specific responsibility.

    Final determination
    The current implementation is non-compliant with the step 4.3 responsibility split implied by Step 4 in src/plan/breadcrumb-implementation-plan.md.

    NodeBody does not yet function as the clean shared inner-body implementation boundary.
    CustomNode still owns responsibilities that should have moved into NodeBody.
    BreadcrumbNode does not yet depend on NodeBody at all and does not enforce the breadcrumb-specific handle policy required by the plan.
*/

// NodeBody is nu verantwoordelijk voor het renderen van de content in de node
// Custom node is de wrapper waarbij de handles worden gerenderd en NodeBody wordt aangeroepen
// BreadcrumbsNode begrijp ik nog niet wat ik doen moet
