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

export const DEFAULT_CONNECTOR_STYLE = "curved";

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
