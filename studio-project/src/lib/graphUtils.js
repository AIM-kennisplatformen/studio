/* Copied from PoC-Robert-React-Flow */

// Helper function to calculate which handles to connect to based on shortest distance
export function getEdgeHandles(sourceX, sourceY, targetX, targetY, nodeWidth = 160, nodeHeight = 80, sourceScale = 1, targetScale = 1) {
  // Apply scale to node dimensions for visual accuracy
  const scaledSourceWidth = nodeWidth * sourceScale;
  const scaledSourceHeight = nodeHeight * sourceScale;
  const scaledTargetWidth = nodeWidth * targetScale;
  const scaledTargetHeight = nodeHeight * targetScale;
  
  // Define handle positions relative to node center
  const sourceHandles = {
    top: { x: sourceX, y: sourceY - scaledSourceHeight / 2, name: 'top' },
    bottom: { x: sourceX, y: sourceY + scaledSourceHeight / 2, name: 'bottom' },
    left: { x: sourceX - scaledSourceWidth / 2, y: sourceY, name: 'left' },
    right: { x: sourceX + scaledSourceWidth / 2, y: sourceY, name: 'right' },
  };
  
  const targetHandles = {
    top: { x: targetX, y: targetY - scaledTargetHeight / 2, name: 'target-top' },
    bottom: { x: targetX, y: targetY + scaledTargetHeight / 2, name: 'target-bottom' },
    left: { x: targetX - scaledTargetWidth / 2, y: targetY, name: 'target-left' },
    right: { x: targetX + scaledTargetWidth / 2, y: targetY, name: 'target-right' },
  };
  
  // Find the pair of handles with the shortest distance
  let minDistance = Infinity;
  let bestSourceHandle = 'right';
  let bestTargetHandle = 'target-left';
  
  Object.values(sourceHandles).forEach(sourceHandle => {
    Object.values(targetHandles).forEach(targetHandle => {
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
        case 'musician':
          return { emoji: '👤', color: '#4CAF50', bgColor: '#E8F5E9' };
        case 'band':
          return { emoji: '🎸', color: '#FF5722', bgColor: '#FFEBE9' };
        case 'song':
          return { emoji: '🎵', color: '#2196F3', bgColor: '#E3F2FD' };
        case 'genre':
          return { emoji: '🎼', color: '#9C27B0', bgColor: '#F3E5F5' };
        case 'instrument':
          return { emoji: '🎹', color: '#FF9800', bgColor: '#FFF3E0' };
        default:
          return { emoji: '⭐', color: '#607D8B', bgColor: '#ECEFF1' };
      }
};


// utils/calculateNodeDistances.js
export function calculateNodeDistances(startNodeId, nodes, edges) {
  const distances = new Map();
  const visited = new Set();
  const queue = [];

  // Initialize
  distances.set(startNodeId, 0);
  visited.add(startNodeId);
  queue.push(startNodeId);

  // Build adjacency list
  const adjacency = new Map();
  edges.forEach(edge => {
    if (!adjacency.has(edge.source)) adjacency.set(edge.source, []);
    if (!adjacency.has(edge.target)) adjacency.set(edge.target, []);
    adjacency.get(edge.source).push(edge.target);
    adjacency.get(edge.target).push(edge.source); // treat as undirected
  });

  // Breadth-first search (BFS)
  while (queue.length > 0) {
    const currentId = queue.shift();
    const currentDistance = distances.get(currentId);

    const neighbors = adjacency.get(currentId) || [];
    for (const neighborId of neighbors) {
      if (!visited.has(neighborId)) {
        visited.add(neighborId);
        distances.set(neighborId, currentDistance + 1);
        queue.push(neighborId);
      }
    }
  }

  // Unreachable nodes get Infinity
  nodes.forEach(node => {
    if (!distances.has(node.id)) {
      distances.set(node.id, Infinity);
    }
  });

  return distances;
}


