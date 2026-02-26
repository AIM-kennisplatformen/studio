/* Copied from PoC-Robert-React-Flow */
// Helper function to calculate which handles to connect to based on shortest distance
export function getEdgeHandles( sourceX,
  sourceY,
  targetX,
  targetY,
  nodeWidth = 160,
  nodeHeight = 80,
  sourceScale = 1,
  targetScale = 1
) {
   // Apply scale to node dimensions for visual accuracy
  const scaledSourceWidth = nodeWidth * sourceScale;
  const scaledSourceHeight = nodeHeight * sourceScale;
  const scaledTargetWidth = nodeWidth * targetScale;
  const scaledTargetHeight = nodeHeight * targetScale;

  // Define handle positions relative to node center
  const sourceHandles = {
    top: { x: sourceX, y: sourceY - scaledSourceHeight / 2, name: "top" },
    bottom: { x: sourceX, y: sourceY + scaledSourceHeight / 2, name: "bottom" },
    left: { x: sourceX - scaledSourceWidth / 2, y: sourceY, name: "left" },
    right: { x: sourceX + scaledSourceWidth / 2, y: sourceY, name: "right" },
  };

  const targetHandles = {
    top: {
      x: targetX,
      y: targetY - scaledTargetHeight / 2,
      name: "target-top",
    },
    bottom: {
      x: targetX,
      y: targetY + scaledTargetHeight / 2,
      name: "target-bottom",
    },
    left: {
      x: targetX - scaledTargetWidth / 2,
      y: targetY,
      name: "target-left",
    },
    right: {
      x: targetX + scaledTargetWidth / 2,
      y: targetY,
      name: "target-right",
    },
  };

  // Find the pair of handles with the shortest distance
  let minDistance = Infinity;
  let bestSourceHandle = "right";
  let bestTargetHandle = "target-left";

  Object.values(sourceHandles).forEach((sourceHandle) => {
    Object.values(targetHandles).forEach((targetHandle) => {
      const dx = targetHandle.x - sourceHandle.x;
      const dy = targetHandle.y - sourceHandle.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance < minDistance) {
        minDistance = distance;
        bestSourceHandle = sourceHandle.name;
        bestTargetHandle = targetHandle.name;
      }
    });
  });

  return { sourceHandle: bestSourceHandle, targetHandle: bestTargetHandle };
}

// Helper function to get emoji and color based on entity type
export const getEntityStyle = (type) => {
  switch (type) {
    default:
      return { emoji: "🖹", color: "#607D8B", bgColor: "#ECEFF1" };
  }
};

export function calculateNodeDistances(selectedNodeId, nodes, edges) {
  if (!Array.isArray(nodes) || !Array.isArray(edges)) {
        return new Map(); // Return an empty Map if data is missing
    }
  // Create adjacency list for the graph
  const adjacencyList = new Map();

  // Initialize adjacency list for all nodes
  nodes.forEach((node) => {
    adjacencyList.set(node.id, []);
  });

  // Build adjacency list from edges (treating graph as undirected)
  edges.forEach((edge) => {
    const sourceNeighbors = adjacencyList.get(edge.source) || [];
    const targetNeighbors = adjacencyList.get(edge.target) || [];

    if (!sourceNeighbors.includes(edge.target)) {
      sourceNeighbors.push(edge.target);
    }
    if (!targetNeighbors.includes(edge.source)) {
      targetNeighbors.push(edge.source);
    }

    adjacencyList.set(edge.source, sourceNeighbors);
    adjacencyList.set(edge.target, targetNeighbors);
  });

  // BFS to calculate distances
  const distances = new Map();
  const queue = [[selectedNodeId, 0]]; // [nodeId, distance]
  const visited = new Set([selectedNodeId]);

  distances.set(selectedNodeId, 0);

  while (queue.length > 0) {
    const [currentNodeId, currentDistance] = queue.shift();

    const neighbors = adjacencyList.get(currentNodeId) || [];

    for (const neighborId of neighbors) {
      if (!visited.has(neighborId)) {
        visited.add(neighborId);
        const neighborDistance = currentDistance + 1;
        distances.set(neighborId, neighborDistance);
        queue.push([neighborId, neighborDistance]);
      }
    }
  }

  // Set infinite distance for unreachable nodes
  nodes.forEach((node) => {
    if (!distances.has(node.id)) {
      distances.set(node.id, Infinity);
    }
  });

  return distances;
}

export function updateEdgePositions(currentEdges, currentNodes) {
  // Create a map for quick node lookup
  const safeCurrentNodes = Array.isArray(currentNodes) ? currentNodes : [];
  const nodeMap = new Map(safeCurrentNodes.map((n) => [n.id, n]));

  return currentEdges.map((edge) => {
    const sourceNode = nodeMap.get(edge.source);
    const targetNode = nodeMap.get(edge.target);

    if (!sourceNode || !targetNode) return edge;

     // Use fixed width since scaling is done via CSS transform
    const { sourceHandle, targetHandle } = getEdgeHandles(
      sourceNode.position.x,
      sourceNode.position.y,
      targetNode.position.x,
      targetNode.position.y,
      160, // Fixed width
      80 // Fixed height
    );
    //Hardcode handles for dagre layout.
    return {
      ...edge,
       sourceHandle,
      targetHandle,
    };
  });
}
