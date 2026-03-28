function dedupeBreadcrumbEntries(breadcrumbEntries) {
  return breadcrumbEntries.reduce((path, entry) => {
    const existingIndex = path.findIndex(
      (pathEntry) => pathEntry.originNodeId === entry.originNodeId
    );

    if (existingIndex >= 0) {
      return path.slice(0, existingIndex + 1);
    }

    return [...path, entry];
  }, []);
}

export function buildBreadcrumbRenderGraph(
  breadcrumbEntries,
  viewport,
  containerWidth
) {
  const dedupedEntries = dedupeBreadcrumbEntries(breadcrumbEntries);

  const nodes = dedupedEntries.map((entry, index) => {
    const screenX = 20 + index * (160 + 24);
    const screenY = 20;
    const flowPosition = {
      x: (screenX - viewport.x) / viewport.zoom,
      y: (screenY - viewport.y) / viewport.zoom,
    };

    return {
      id: entry.historyId, // e.g. "bc-0"
      type: "breadcrumb", // registered node type
      position: flowPosition, // computed above
      draggable: false, // breadcrumbs must not be dragged
      selectable: false, // prevent selection rectangle interaction
      connectable: false, // prevent manual edge creation
      data: {
        label: entry.label,
        originNodeId: entry.originNodeId,
        // Copy visual styling similar to real nodes:
        background: "#ffffff",
        color: "#038061",
        border: "2px solid #038061",
        borderRadius: "8px",
        padding: "8px",
        fontSize: "12px",
        width: 160,
        whiteSpace: "pre-wrap",
        boxShadow: "0 4px 8px rgba(0,0,0,0.1)",
      },
      style: { zIndex: 2000 }, // above regular nodes (which default to 0; selected ones use 1000)
    };
  });

  const edges = dedupedEntries.slice(0, -1).map((entry, index) => ({
    id: `bc-edge-${entry.historyId}-${dedupedEntries[index + 1].historyId}`,
    source: entry.historyId,
    target: dedupedEntries[index + 1].historyId,
    type: "solid",
    sourceHandle: "right",
    targetHandle: "target-left",
    style: { stroke: "#038061", strokeWidth: 1.5, strokeDasharray: "6 3" },
    zIndex: 1500,
  }));

  return { nodes, edges };
}

export function buildBridgeEdge(breadcrumbEntries, anchorNodeId) {
  const dedupedEntries = dedupeBreadcrumbEntries(breadcrumbEntries);

  if (!dedupedEntries.length || anchorNodeId == null) {
    return null;
  }

  const lastEntry = dedupedEntries[dedupedEntries.length - 1];

  return {
    id: `bc-bridge-${lastEntry.historyId}-${String(anchorNodeId)}`,
    source: lastEntry.historyId,
    target: String(anchorNodeId),
    type: "solid",
    sourceHandle: "bottom",
    targetHandle: "target-top",
    style: {
      stroke: "#038061",
      strokeWidth: 2,
      strokeDasharray: "4 4",
      opacity: 0.6,
    },
    zIndex: 1500,
  };
}
