/* Copied from PoC-Robert-React-Flow */
// Helper function to calculate which handles to connect to based on shortest distance
export function getEdgeHandles() {
  // Always use bottom for source and top for target
  return { sourceHandle: 'bottom', targetHandle: 'target-top' }
}

// Helper function to get emoji and color based on entity type
export const getEntityStyle = (type) => {
  switch (type) {
    default:
      return { emoji: '🖹', color: '#607D8B', bgColor: '#ECEFF1' }
  }
}

export function calculateNodeDistances(selectedNodeId, nodes, edges) {
  if (!Array.isArray(nodes) || !Array.isArray(edges)) {
    return new Map() // Return an empty Map if data is missing
  }
  // Create adjacency list for the graph
  const adjacencyList = new Map()

  // Initialize adjacency list for all nodes
  nodes.forEach((node) => {
    adjacencyList.set(node.id, [])
  })

  // Build adjacency list from edges (treating graph as undirected)
  edges.forEach((edge) => {
    const sourceNeighbors = adjacencyList.get(edge.source) || []
    const targetNeighbors = adjacencyList.get(edge.target) || []

    if (!sourceNeighbors.includes(edge.target)) {
      sourceNeighbors.push(edge.target)
    }
    if (!targetNeighbors.includes(edge.source)) {
      targetNeighbors.push(edge.source)
    }

    adjacencyList.set(edge.source, sourceNeighbors)
    adjacencyList.set(edge.target, targetNeighbors)
  })

  // BFS to calculate distances
  const distances = new Map()
  const queue = [[selectedNodeId, 0]] // [nodeId, distance]
  const visited = new Set([selectedNodeId])

  distances.set(selectedNodeId, 0)

  while (queue.length > 0) {
    const [currentNodeId, currentDistance] = queue.shift()

    const neighbors = adjacencyList.get(currentNodeId) || []

    for (const neighborId of neighbors) {
      if (!visited.has(neighborId)) {
        visited.add(neighborId)
        const neighborDistance = currentDistance + 1
        distances.set(neighborId, neighborDistance)
        queue.push([neighborId, neighborDistance])
      }
    }
  }

  // Set infinite distance for unreachable nodes
  nodes.forEach((node) => {
    if (!distances.has(node.id)) {
      distances.set(node.id, Infinity)
    }
  })

  return distances
}

export function updateEdgePositions(currentEdges, currentNodes) {
  // Create a map for quick node lookup
  const safeCurrentNodes = Array.isArray(currentNodes) ? currentNodes : []
  const nodeMap = new Map(safeCurrentNodes.map((n) => [n.id, n]))

  return currentEdges.map((edge) => {
    const sourceNode = nodeMap.get(edge.source)
    const targetNode = nodeMap.get(edge.target)

    if (!sourceNode || !targetNode) return edge

    //Hardcode handles for dagre layout.
    return {
      ...edge,
      sourceHandle: 'bottom',
      targetHandle: 'target-top',
    }
  })
}
