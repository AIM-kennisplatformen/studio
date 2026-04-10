export const CONNECTOR_STYLE_CONFIG = {
  solid: {
    key: "solid",
    label: "Solid",
    edgeType: "bridgeConnector",
    strokeDasharray: "none",
    pathVariant: "smooth",
  },
  dashed: {
    key: "dashed",
    label: "Dashed",
    edgeType: "bridgeConnector",
    strokeDasharray: "10 6",
    pathVariant: "smooth",
  },
  step: {
    key: "step",
    label: "Step",
    edgeType: "bridgeConnector",
    strokeDasharray: "2 6",
    pathVariant: "smooth",
  },
  curved: {
    key: "curved",
    label: "Curved",
    edgeType: "bridgeConnector",
    strokeDasharray: "none",
    pathVariant: "bezier",
  },
  straight: {
    key: "straight",
    label: "Straight",
    edgeType: "bridgeConnector",
    strokeDasharray: "none",
    pathVariant: "straight",
  },
};

export const DEFAULT_CONNECTOR_STYLE = "solid";

export function getConnectorStyleConfig(connectorStyle) {
  return (
    CONNECTOR_STYLE_CONFIG[connectorStyle] ||
    CONNECTOR_STYLE_CONFIG[DEFAULT_CONNECTOR_STYLE]
  );
}

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
  anchorNode = null
) {
  const dedupedEntries = dedupeBreadcrumbEntries(breadcrumbEntries);
  const nodeHeight = 160;
  const rowGap = 24;
  const verticalStep = nodeHeight + rowGap;
  const hasAnchorNode = Number.isFinite(anchorNode?.y);
  const newestIndex = dedupedEntries.length - 1;
  const newestScreenY = hasAnchorNode
    ? viewport.y + anchorNode.y * viewport.zoom
    : 20 + newestIndex * verticalStep;

  const nodes = dedupedEntries.map((entry, index) => {
    const screenX = 20;
    const levelsAboveNewest = newestIndex - index;
    const screenY = newestScreenY - levelsAboveNewest * verticalStep;
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
        padding: "2px",
        fontSize: "8px",
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
    type: "step",
    sourceHandle: "bottom",
    targetHandle: "target-top",
    style: { stroke: "#038061", strokeWidth: 1.5, strokeDasharray: "2 3" },
    zIndex: 1500,
  }));

  return { nodes, edges };
}

export function buildBridgeEdge(
  breadcrumbEntries,
  anchorNodeId,
  connectorStyle = DEFAULT_CONNECTOR_STYLE
) {
  const dedupedEntries = dedupeBreadcrumbEntries(breadcrumbEntries);

  if (!dedupedEntries.length || anchorNodeId == null) {
    return null;
  }

  const lastEntry = dedupedEntries[dedupedEntries.length - 1];
  const connectorConfig = getConnectorStyleConfig(connectorStyle);

  return {
    id: `bc-bridge-${lastEntry.historyId}-${String(anchorNodeId)}`,
    source: lastEntry.historyId,
    target: String(anchorNodeId),
    type: connectorConfig.edgeType,
    sourceHandle: "right",
    targetHandle: "target-left",
    style: {
      stroke: "#038061",
      strokeWidth: 2,
      strokeDasharray: connectorConfig.strokeDasharray,
      opacity: 0.6,
    },
    data: {
      connectorStyle: connectorConfig.key,
      pathVariant: connectorConfig.pathVariant,
    },
    zIndex: 1500,
  };
}
