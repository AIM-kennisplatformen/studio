import { useState, useCallback, useRef, useEffect } from 'react';
import { useReactFlow } from '@xyflow/react';
import { applyAvsdfLayout, applyColaLayout, applyFcoseLayout } from '@/lib/ctrytoscapeLayout';
/**
 * Custom hook to handle node position animations in React Flow
 * @param {Array} nodes - Current nodes array
 * @param {Array} edges - Current edges array
 * @param {Function} setNodes - Function to update nodes
 * @param {Function} setEdges - Function to update edges
 * @param {Function} updateEdgePositions - Function to update edge positions based on node positions
 * @returns {Object} - Animation controls and state
 */
export function useFlowAnimation(nodes, edges, setNodes, setEdges, updateEdgePositions) {
  const { setViewport, getViewport } = useReactFlow();
  const animationFrameRef = useRef(null);
  const [isAnimating, setIsAnimating] = useState(false);

  // Function to randomize node positions with smooth animation
  const randomizePositions = useCallback(() => {
    if (nodes.length === 0) return;
    
    // Cancel any ongoing animation
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    setIsAnimating(true);
    
    // Store start positions and generate random target positions
    const startPositions = nodes.map(node => ({ ...node.position }));
    const targetPositions = nodes.map(() => ({
      x: Math.random() * 1500,
      y: Math.random() * 1500,
    }));
    
    // Get the person node index and store initial viewport center
    const personIndex = nodes.findIndex(n => n.id === 'person');
    const initialViewport = getViewport();
    
    const duration = 1000; // Animation duration in milliseconds
    const startTime = Date.now();
    
    // Animation loop using requestAnimationFrame
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function (ease-out cubic for smooth deceleration)
      const eased = 1 - Math.pow(1 - progress, 3);
      
      // Check if remaining movement is negligible (sub-pixel)
      let maxRemainingMovement = 0;
      for (let i = 0; i < startPositions.length; i++) {
        if (startPositions[i] && targetPositions[i]) {
          const remainingX = Math.abs((targetPositions[i].x - startPositions[i].x) * (1 - eased));
          const remainingY = Math.abs((targetPositions[i].y - startPositions[i].y) * (1 - eased));
          maxRemainingMovement = Math.max(maxRemainingMovement, remainingX, remainingY);
        }
      }
      
      // If all nodes have essentially stopped moving (< 0.5 pixels), end animation early
      const isEffectivelyComplete = maxRemainingMovement < 0.5;
      
      // Update all node positions at once
      setNodes((currentNodes) => {
        const updatedNodes = currentNodes.map((node, index) => {
          if (!startPositions[index] || !targetPositions[index]) return node;
          
          return {
            ...node,
            position: {
              x: isEffectivelyComplete ? targetPositions[index].x : startPositions[index].x + (targetPositions[index].x - startPositions[index].x) * eased,
              y: isEffectivelyComplete ? targetPositions[index].y : startPositions[index].y + (targetPositions[index].y - startPositions[index].y) * eased,
            },
          };
        });
        
        // Update edge positions based on new node positions
        setEdges((currentEdges) => updateEdgePositions(updatedNodes, currentEdges));
        
        return updatedNodes;
      });
      
      // Pan viewport to keep person node at same viewport position
      if (personIndex !== -1) {
        // Calculate how much the person node has moved in world coordinates
        const deltaX = (targetPositions[personIndex].x - startPositions[personIndex].x) * eased;
        const deltaY = (targetPositions[personIndex].y - startPositions[personIndex].y) * eased;
        
        // Adjust viewport position by the same delta to compensate for node movement
        setViewport({
          x: initialViewport.x - deltaX * initialViewport.zoom,
          y: initialViewport.y - deltaY * initialViewport.zoom,
          zoom: initialViewport.zoom
        }, { duration: 0 });
      }
      
      // Continue animation if not complete and still has visible movement
      if (progress < 1 && !isEffectivelyComplete) {
        animationFrameRef.current = requestAnimationFrame(animate);
      } else {
        animationFrameRef.current = null;
        setIsAnimating(false);
      }
    };
    
    // Start the animation
    animationFrameRef.current = requestAnimationFrame(animate);
  }, [nodes, setNodes, setEdges, updateEdgePositions, setViewport, getViewport]);

  // Function to apply avsdf layout with smooth animation
  const applyAvsdfPositions = useCallback(() => {
    if (nodes.length === 0) return;
    
    // Cancel any ongoing animation
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    setIsAnimating(true);
    
    // Store start positions
    const startPositions = nodes.map(node => ({ ...node.position }));
    
    // Get target positions from avsdf layout using cytoscape
    const newPositions = applyAvsdfLayout(nodes, edges, { nodeSeparation: 120 });
    
    // Convert to array format matching nodes order
    const targetPositions = nodes.map(node => newPositions[node.id] || node.position);
    
    // Get the person node index and store initial viewport center
    const personIndex = nodes.findIndex(n => n.id === 'person');
    const initialViewport = getViewport();
    
    const duration = 1000; // Animation duration in milliseconds
    const startTime = Date.now();
    
    // Animation loop using requestAnimationFrame
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function (ease-out cubic for smooth deceleration)
      const eased = 1 - Math.pow(1 - progress, 3);
      
      // Check if remaining movement is negligible (sub-pixel)
      let maxRemainingMovement = 0;
      for (let i = 0; i < startPositions.length; i++) {
        if (startPositions[i] && targetPositions[i]) {
          const remainingX = Math.abs((targetPositions[i].x - startPositions[i].x) * (1 - eased));
          const remainingY = Math.abs((targetPositions[i].y - startPositions[i].y) * (1 - eased));
          maxRemainingMovement = Math.max(maxRemainingMovement, remainingX, remainingY);
        }
      }
      
      // If all nodes have essentially stopped moving (< 0.5 pixels), end animation early
      const isEffectivelyComplete = maxRemainingMovement < 0.5;
      
      // Update all node positions at once
      setNodes((currentNodes) => {
        const updatedNodes = currentNodes.map((node, index) => {
          if (!startPositions[index] || !targetPositions[index]) return node;
          
          return {
            ...node,
            position: {
              x: isEffectivelyComplete ? targetPositions[index].x : startPositions[index].x + (targetPositions[index].x - startPositions[index].x) * eased,
              y: isEffectivelyComplete ? targetPositions[index].y : startPositions[index].y + (targetPositions[index].y - startPositions[index].y) * eased,
            },
          };
        });
        
        // Update edge positions based on new node positions
        setEdges((currentEdges) => updateEdgePositions(updatedNodes, currentEdges));
        
        return updatedNodes;
      });
      
      // Pan viewport to keep person node at same viewport position
      if (personIndex !== -1) {
        // Calculate how much the person node has moved in world coordinates
        const deltaX = (targetPositions[personIndex].x - startPositions[personIndex].x) * eased;
        const deltaY = (targetPositions[personIndex].y - startPositions[personIndex].y) * eased;
        
        // Adjust viewport position by the same delta to compensate for node movement
        setViewport({
          x: initialViewport.x - deltaX * initialViewport.zoom,
          y: initialViewport.y - deltaY * initialViewport.zoom,
          zoom: initialViewport.zoom
        }, { duration: 0 });
      }
      
      // Continue animation if not complete and still has visible movement
      if (progress < 1 && !isEffectivelyComplete) {
        animationFrameRef.current = requestAnimationFrame(animate);
      } else {
        animationFrameRef.current = null;
        setIsAnimating(false);
      }
    };
    
    // Start the animation
    animationFrameRef.current = requestAnimationFrame(animate);
  }, [nodes, edges, setNodes, setEdges, updateEdgePositions, setViewport, getViewport]);

  // Function to apply cola layout with smooth animation
  const applyColaPositions = useCallback(() => {
    if (nodes.length === 0) return;
    
    // Cancel any ongoing animation
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    setIsAnimating(true);
    
    // Store start positions
    const startPositions = nodes.map(node => ({ ...node.position }));
    
    // Get target positions from cola layout using cytoscape
    // Cola will run all iterations synchronously because animate is false
    const newPositions = applyColaLayout(nodes, edges, {
      edgeLength: 150,
      nodeSpacing: 90,
      maxSimulationTime: 4000
    });
    
    // Convert to array format matching nodes order
    const targetPositions = nodes.map(node => newPositions[node.id] || node.position);
    
    // Get the person node index and store initial viewport center
    const personIndex = nodes.findIndex(n => n.id === 'person');
    const initialViewport = getViewport();
    
    const duration = 1000; // Animation duration in milliseconds
    const startTime = Date.now();
    
    // Animation loop using requestAnimationFrame
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function (ease-out cubic for smooth deceleration)
      const eased = 1 - Math.pow(1 - progress, 3);
      
      // Check if remaining movement is negligible (sub-pixel)
      let maxRemainingMovement = 0;
      for (let i = 0; i < startPositions.length; i++) {
        if (startPositions[i] && targetPositions[i]) {
          const remainingX = Math.abs((targetPositions[i].x - startPositions[i].x) * (1 - eased));
          const remainingY = Math.abs((targetPositions[i].y - startPositions[i].y) * (1 - eased));
          maxRemainingMovement = Math.max(maxRemainingMovement, remainingX, remainingY);
        }
      }
      
      // If all nodes have essentially stopped moving (< 0.5 pixels), end animation early
      const isEffectivelyComplete = maxRemainingMovement < 0.5;
      
      // Update all node positions at once
      setNodes((currentNodes) => {
        const updatedNodes = currentNodes.map((node, index) => {
          if (!startPositions[index] || !targetPositions[index]) return node;
          
          return {
            ...node,
            position: {
              x: isEffectivelyComplete ? targetPositions[index].x : startPositions[index].x + (targetPositions[index].x - startPositions[index].x) * eased,
              y: isEffectivelyComplete ? targetPositions[index].y : startPositions[index].y + (targetPositions[index].y - startPositions[index].y) * eased,
            },
          };
        });
        
        // Update edge positions based on new node positions
        setEdges((currentEdges) => updateEdgePositions(updatedNodes, currentEdges));
        
        return updatedNodes;
      });
      
      // Pan viewport to keep person node at same viewport position
      if (personIndex !== -1) {
        // Calculate how much the person node has moved in world coordinates
        const deltaX = (targetPositions[personIndex].x - startPositions[personIndex].x) * eased;
        const deltaY = (targetPositions[personIndex].y - startPositions[personIndex].y) * eased;
        
        // Adjust viewport position by the same delta to compensate for node movement
        setViewport({
          x: initialViewport.x - deltaX * initialViewport.zoom,
          y: initialViewport.y - deltaY * initialViewport.zoom,
          zoom: initialViewport.zoom
        }, { duration: 0 });
      }
      
      // Continue animation if not complete and still has visible movement
      if (progress < 1 && !isEffectivelyComplete) {
        animationFrameRef.current = requestAnimationFrame(animate);
      } else {
        animationFrameRef.current = null;
        setIsAnimating(false);
      }
    };
    
    // Start the animation
    animationFrameRef.current = requestAnimationFrame(animate);
  }, [nodes, edges, setNodes, setEdges, updateEdgePositions, setViewport, getViewport]);

  // Function to apply fcose layout with smooth animation
  const applyFcosePositions = useCallback(() => {
    if (nodes.length === 0) return;
    
    // Cancel any ongoing animation
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    setIsAnimating(true);
    
    // Store start positions
    const startPositions = nodes.map(node => ({ ...node.position }));
    
    // Get target positions from fcose layout using cytoscape
    const newPositions = applyFcoseLayout(nodes, edges, {
      quality: 'proof', // Highest quality for better node placement
      nodeSeparation: 200, // Increased minimum separation
      idealEdgeLength: 300, // Longer ideal edge length
      nodeRepulsion: 50000, // Much stronger repulsion to prevent overlaps
      gravity: 0.05, // Very low gravity to allow maximum spreading
      gravityRange: 5.0, // Larger gravity range
      numIter: 5000, // Many more iterations for convergence
      initialEnergyOnIncremental: 0.3, // Lower initial energy
      tile: true, // Use tiling to prevent overlaps
      tilingPaddingVertical: 20,
      tilingPaddingHorizontal: 20
    });
    
    // Convert to array format matching nodes order
    const targetPositions = nodes.map(node => newPositions[node.id] || node.position);
    
    // Get the person node index and store initial viewport center
    const personIndex = nodes.findIndex(n => n.id === 'person');
    const initialViewport = getViewport();
    
    const duration = 1000; // Animation duration in milliseconds
    const startTime = Date.now();
    
    // Animation loop using requestAnimationFrame
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function (ease-out cubic for smooth deceleration)
      const eased = 1 - Math.pow(1 - progress, 3);
      
      // Check if remaining movement is negligible (sub-pixel)
      let maxRemainingMovement = 0;
      for (let i = 0; i < startPositions.length; i++) {
        if (startPositions[i] && targetPositions[i]) {
          const remainingX = Math.abs((targetPositions[i].x - startPositions[i].x) * (1 - eased));
          const remainingY = Math.abs((targetPositions[i].y - startPositions[i].y) * (1 - eased));
          maxRemainingMovement = Math.max(maxRemainingMovement, remainingX, remainingY);
        }
      }
      
      // If all nodes have essentially stopped moving (< 0.5 pixels), end animation early
      const isEffectivelyComplete = maxRemainingMovement < 0.5;
      
      // Update all node positions at once
      setNodes((currentNodes) => {
        const updatedNodes = currentNodes.map((node, index) => {
          if (!startPositions[index] || !targetPositions[index]) return node;
          
          return {
            ...node,
            position: {
              x: isEffectivelyComplete ? targetPositions[index].x : startPositions[index].x + (targetPositions[index].x - startPositions[index].x) * eased,
              y: isEffectivelyComplete ? targetPositions[index].y : startPositions[index].y + (targetPositions[index].y - startPositions[index].y) * eased,
            },
          };
        });
        
        // Update edge positions based on new node positions
        setEdges((currentEdges) => updateEdgePositions(updatedNodes, currentEdges));
        
        return updatedNodes;
      });
      
      // Pan viewport to keep person node at same viewport position
      if (personIndex !== -1) {
        // Calculate how much the person node has moved in world coordinates
        const deltaX = (targetPositions[personIndex].x - startPositions[personIndex].x) * eased;
        const deltaY = (targetPositions[personIndex].y - startPositions[personIndex].y) * eased;
        
        // Adjust viewport position by the same delta to compensate for node movement
        setViewport({
          x: initialViewport.x - deltaX * initialViewport.zoom,
          y: initialViewport.y - deltaY * initialViewport.zoom,
          zoom: initialViewport.zoom
        }, { duration: 0 });
      }
      
      // Continue animation if not complete and still has visible movement
      if (progress < 1 && !isEffectivelyComplete) {
        animationFrameRef.current = requestAnimationFrame(animate);
      } else {
        animationFrameRef.current = null;
        setIsAnimating(false);
      }
    };
    
    // Start the animation
    animationFrameRef.current = requestAnimationFrame(animate);
  }, [nodes, edges, setNodes, setEdges, updateEdgePositions, setViewport, getViewport]);

  // Cleanup animation on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Function to stop any ongoing animation
  const stopAnimation = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
      setIsAnimating(false);
    }
  }, []);

  return {
    randomizePositions,
    applyAvsdfPositions,
    applyColaPositions,
    applyFcosePositions,
    stopAnimation,
    isAnimating
  };
}