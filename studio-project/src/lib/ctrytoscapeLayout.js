/* Copied from PoC-Robert-React-Flow */
import cytoscape from 'cytoscape';
import avsdf from 'cytoscape-avsdf';
import cola from 'cytoscape-cola';
import fcose from 'cytoscape-fcose';

// Register the layout extensions
cytoscape.use(avsdf);
cytoscape.use(cola);
cytoscape.use(fcose);

/**
 * Convert React Flow nodes and edges to Cytoscape format
 * @param {Array} nodes - React Flow nodes
 * @param {Array} edges - React Flow edges
 * @returns {Array} Cytoscape elements array
 */
function reactFlowToCytoscape(nodes, edges, includeNodeSize = false) {
  const cytoscapeElements = [];
  
  // Convert nodes
  nodes.forEach(node => {
    const nodeData = { id: node.id };
    
    // Add node dimensions if requested (for layouts that support it like fcose)
    if (includeNodeSize) {
      // Use the width from node data, or default to 160
      const width = node.data?.width || 160;
      // Estimate height based on label content (approximate)
      const height = 80; // Approximate height for our nodes
      
      nodeData.width = width;
      nodeData.height = height;
    }
    
    cytoscapeElements.push({
      group: 'nodes',
      data: nodeData,
      position: { x: node.position.x, y: node.position.y }
    });
  });
  
  // Convert edges
  edges.forEach(edge => {
    cytoscapeElements.push({
      group: 'edges',
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target
      }
    });
  });
  
  return cytoscapeElements;
}

/**
 * Apply avsdf layout using cytoscape.js in headless mode
 * @param {Array} nodes - React Flow nodes
 * @param {Array} edges - React Flow edges
 * @param {Object} options - Layout options (optional)
 * @returns {Object} Map of node IDs to new positions
 */
export function applyAvsdfLayout(nodes, edges, options = {}) {
  // Create headless cytoscape instance
  const cy = cytoscape({
    headless: true,
    elements: reactFlowToCytoscape(nodes, edges)
  });
  
  // Run avsdf layout with options
  const layout = cy.layout({
    name: 'avsdf',
    // Default options for avsdf
    nodeSeparation: options.nodeSeparation || 60,
    // Disable animations since we handle them in React
    animate: false,
    ...options
  });
  
  // Run the layout synchronously
  layout.run();
  
  // Extract new positions
  const newPositions = {};
  cy.nodes().forEach(node => {
    const pos = node.position();
    newPositions[node.id()] = {
      x: pos.x,
      y: pos.y
    };
  });
  
  return newPositions;
}

/**
 * Update React Flow nodes with new positions from layout
 * @param {Array} nodes - Original React Flow nodes
 * @param {Object} newPositions - Map of node IDs to positions
 * @returns {Array} Updated nodes array
 */
export function updateNodePositions(nodes, newPositions) {
  return nodes.map(node => ({
    ...node,
    position: newPositions[node.id] || node.position
  }));
}

/**
 * Apply cola layout using cytoscape.js in headless mode
 * Cola is a continuous/iterative layout that runs all iterations synchronously when animate is false
 * @param {Array} nodes - React Flow nodes
 * @param {Array} edges - React Flow edges
 * @param {Object} options - Layout options (optional)
 * @returns {Object} Map of node IDs to new positions
 */
export function applyColaLayout(nodes, edges, options = {}) {
  // Create headless cytoscape instance
  const cy = cytoscape({
    headless: true,
    elements: reactFlowToCytoscape(nodes, edges)
  });
  
  // Run cola layout with options
  const layout = cy.layout({
    name: 'cola',
    // Disable animations - this makes cola run all iterations synchronously
    animate: false,
    // Default options for cola
    maxSimulationTime: options.maxSimulationTime || 4000, // Max time for layout
    ungrabifyWhileSimulating: false,
    fit: true,
    // Edge length and node spacing
    edgeLength: options.edgeLength || 100,
    nodeSpacing: options.nodeSpacing || 50,
    // Convergence parameters
    convergenceThreshold: options.convergenceThreshold || 0.01,
    ...options
  });
  
  // Run the layout synchronously - all iterations complete before returning
  layout.run();
  
  // Extract new positions
  const newPositions = {};
  cy.nodes().forEach(node => {
    const pos = node.position();
    newPositions[node.id()] = {
      x: pos.x,
      y: pos.y
    };
  });
  
  return newPositions;
}

/**
 * Apply fcose layout using cytoscape.js in headless mode
 * fCoSE (fast Compound Spring Embedder) is a fast, high-quality layout algorithm
 * @param {Array} nodes - React Flow nodes
 * @param {Array} edges - React Flow edges
 * @param {Object} options - Layout options (optional)
 * @returns {Object} Map of node IDs to new positions
 */
export function applyFcoseLayout(nodes, edges, options = {}) {
  // Create headless cytoscape instance with node dimensions
  const cy = cytoscape({
    headless: true,
    elements: reactFlowToCytoscape(nodes, edges, true) // Include node sizes
  });
  
  // Run fcose layout with options
  const layout = cy.layout({
    name: 'fcose',
    // Disable animations - layout runs synchronously
    animate: false,
    // Default options for fcose
    quality: options.quality || 'default', // 'draft', 'default', or 'proof'
    randomize: options.randomize !== undefined ? options.randomize : true,
    nodeSeparation: options.nodeSeparation || 75,
    idealEdgeLength: options.idealEdgeLength || 150,
    edgeElasticity: options.edgeElasticity || 0.45,
    nestingFactor: options.nestingFactor || 0.1,
    gravity: options.gravity || 0.25,
    numIter: options.numIter || 2500,
    // Enable node dimensions to prevent overlaps
    nodeDimensionsIncludeLabels: false,
    uniformNodeDimensions: false,
    packComponents: true, // Pack connected components
    ...options
  });
  
  // Run the layout synchronously
  layout.run();
  
  // Extract new positions
  const newPositions = {};
  cy.nodes().forEach(node => {
    const pos = node.position();
    newPositions[node.id()] = {
      x: pos.x,
      y: pos.y
    };
  });
  
  return newPositions;
}