import { useCallback, useEffect } from 'react';
import { ReactFlow, applyEdgeChanges, addEdge, useReactFlow } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './App.css';
import { Button } from './components/ui/button';
import { CustomNode } from './components/CustomNode';
import { getEntityStyle, getEdgeHandles } from './lib/graphUtils';
import { useAtom } from 'jotai';
import { nodesAtom, edgesAtom, draggingNodeIdAtom, selectedNodeAtom } from './data/atoms';
import { useFlowAnimation } from './hooks/useFlowAnimation';
import { applyNodeChanges } from '@xyflow/react';
import { calculateNodeDistances } from './lib/graphUtils';
import { applyFcoseLayout } from './lib/ctrytoscapeLayout';


export default function Graph({ data, width }) {
const [nodes, setNodes] = useAtom(nodesAtom);
  const [edges, setEdges] = useAtom(edgesAtom);
  const [draggingNodeId, setDraggingNodeId] = useAtom(draggingNodeIdAtom);
  const [selectedNode, setSelectedNode] = useAtom(selectedNodeAtom);
  const { setViewport, getViewport, updateNodeInternals } = useReactFlow();
  
  // Convert knowledge graph data to React Flow nodes and edges
  useEffect(() => {
    if (!data || !data.allNodes || !data.allEdges) return;
    
    const newNodes = [];
    const newEdges = [];
    
    // Create nodes from all entities with placeholder positioning
    const nodeMap = new Map();
    data.allNodes.forEach((node) => {
      const style = getEntityStyle(node.type);
      
      const reactFlowNode = {
        id: String(node.id),
        type: 'custom',
        position: { x: 0, y: 0 }, // Placeholder - will be set by fCoSE
        data: {
          label: `${node.title}\n${node.released !== 'N/A' ? `(${node.released})` : ''}`,
          background: style.bgColor,
          color: '#333',
          border: `2px solid ${style.color}`,
          borderRadius: '8px',
          padding: '8px',
          fontSize: '12px',
          width: 160,
          whiteSpace: 'pre-wrap',
          boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
        }
      };
      newNodes.push(reactFlowNode);
      nodeMap.set(reactFlowNode.id, reactFlowNode);
    });
    
    // Create edges from all relationships with smart handle positioning
    data.allEdges.forEach((edge) => {
      const sourceNode = nodeMap.get(String(edge.source));
      const targetNode = nodeMap.get(String(edge.target));
      
      if (sourceNode && targetNode) {
        const { sourceHandle, targetHandle } = getEdgeHandles(
          sourceNode.position.x,
          sourceNode.position.y,
          targetNode.position.x,
          targetNode.position.y
        );
        
        const reactFlowEdge = {
          id: String(edge.id),
          source: String(edge.source),
          target: String(edge.target),
          label: edge.label_forward,
          type: 'default',
          animated: false,
          sourceHandle,
          targetHandle,
          markerEnd: {
            type: 'arrowclosed',
            color: '#999',
          },
          style: { stroke: '#999', strokeWidth: 1.5 },
          labelStyle: {
            fill: '#666',
            fontSize: '10px',
            fontWeight: 'normal',
          },
          labelBgStyle: { fill: 'white', fillOpacity: 0.8 },
        };
        newEdges.push(reactFlowEdge);
      }
    });
    
    // Apply fCoSE layout to get initial positions
    const fcosePositions = applyFcoseLayout(newNodes, newEdges, {
      quality: 'proof',
      nodeSeparation: 200,
      idealEdgeLength: 300,
      nodeRepulsion: 50000,
      gravity: 0.05,
      gravityRange: 5.0,
      numIter: 5000,
      initialEnergyOnIncremental: 0.3,
      tile: true,
      tilingPaddingVertical: 20,
      tilingPaddingHorizontal: 20
    });
    
    // Apply fCoSE positions to nodes
    const nodesWithPositions = newNodes.map(node => ({
      ...node,
      position: fcosePositions[node.id] || node.position
    }));
    
    // Update React Flow state with positioned nodes
    setNodes(nodesWithPositions);
    setEdges(newEdges);
    
  }, [data]);

  // Function to update edge handles based on node positions
  const updateEdgePositions = useCallback((currentNodes, currentEdges) => {
    // Create a map for quick node lookup
    const nodeMap = new Map(currentNodes.map(n => [n.id, n]));

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
        80   // Fixed height
      );

      return {
        ...edge,
        sourceHandle,
        targetHandle,
      };
    });
  }, []);

  // Update node and edge styling based on selection
  useEffect(() => {
    if (selectedNode) {
      // Calculate distances from selected node
      const distances = calculateNodeDistances(selectedNode.id, nodes, edges);
      
      // Track which nodes will change their scale (for updateNodeInternals)
      const nodesNeedingUpdate = new Set();
      
      // Update nodes with distance information only (no width changes)
      setNodes(currentNodes => {
        const updatedNodes = currentNodes.map(node => {
          const distance = distances.get(node.id) ?? Infinity;
          const previousDistance = node.data.distance ?? null;
          
          // Track if this node's scale will change
          const wasSelected = previousDistance === 0;
          const isSelected = distance === 0;
          if (wasSelected !== isSelected) {
            nodesNeedingUpdate.add(node.id);
          }
          
          return {
            ...node,
            data: {
              ...node.data,
              distance,
            },
          };
        });
        
        // Update edge styling (positions don't change since we use fixed widths)
        setEdges(currentEdges => {
          return currentEdges.map(edge => {
            const sourceDistance = distances.get(edge.source) ?? Infinity;
            const targetDistance = distances.get(edge.target) ?? Infinity;
            
            // Edge is connected if it connects to the selected node (distance 0)
            const isConnected = sourceDistance === 0 || targetDistance === 0;
            
            // Both nodes are distant (distance > 1)
            const bothDistant = sourceDistance > 1 && targetDistance > 1;
            
            // Determine edge color
            let strokeColor = '#999'; // default gray
            if (isConnected) {
              strokeColor = '#1a73e8'; // blue for connected
            } else if (bothDistant) {
              strokeColor = 'var(--distant-edge-color)'; // persimmon/tomato for distant
            }
            
            return {
              ...edge,
              animated: isConnected,
              style: {
                ...edge.style,
                stroke: strokeColor,
                strokeWidth: isConnected ? 2.5 : 1.5,
              },
              labelStyle: {
                ...edge.labelStyle,
                opacity: bothDistant ? 0 : 1,
              },
              labelBgStyle: {
                ...edge.labelBgStyle,
                fillOpacity: bothDistant ? 0 : 0.8,
              },
            };
          });
        });
        
        // Update React Flow's internal node measurements after state update
        setTimeout(() => {
          nodesNeedingUpdate.forEach(nodeId => {
            updateNodeInternals(nodeId);
          });
        }, 50);
        
        return updatedNodes;
      });
    } else {
      // Track which nodes were selected (for updateNodeInternals)
      const nodesNeedingUpdate = new Set();
      
      // Reset all nodes to remove distance data
      setNodes(currentNodes => {
        const resetNodes = currentNodes.map(node => {
          // Track if this node was selected before
          if (node.data.distance === 0) {
            nodesNeedingUpdate.add(node.id);
          }
          
          return {
            ...node,
            data: {
              ...node.data,
              distance: null,
            },
          };
        });
        
        // Reset edge styling
        setEdges(currentEdges => {
          return currentEdges.map(edge => ({
            ...edge,
            animated: false,
            style: {
              stroke: '#999',
              strokeWidth: 1.5,
            },
            labelStyle: {
              fill: '#666',
              fontSize: '10px',
              fontWeight: 'normal',
              opacity: 1,
            },
            labelBgStyle: {
              fill: 'white',
              fillOpacity: 0.8,
            },
          }));
        });
        
        // Update React Flow's internal node measurements after state update
        setTimeout(() => {
          nodesNeedingUpdate.forEach(nodeId => {
            updateNodeInternals(nodeId);
          });
        }, 50);
        
        return resetNodes;
      });
    }
  }, [selectedNode, updateEdgePositions, updateNodeInternals]);

  // Use the custom animation hook
  const { randomizePositions, applyAvsdfPositions, applyColaPositions, applyFcosePositions, isAnimating } = useFlowAnimation(nodes, edges, setNodes, setEdges, updateEdgePositions);
  
  const onNodesChange = useCallback(
    (changes) => {
      setNodes((nodesSnapshot) => {
        let filteredChanges = changes;
        
        // Check change types in this batch
        const hasPositionChanges = changes.some(change => change.type === 'position');
        const selectChanges = changes.filter(change => change.type === 'select');
        const deselectChanges = selectChanges.filter(c => !c.selected);
        
        // Detect node selection
        const selectedChange = selectChanges.find(c => c.selected);
        if (selectedChange) {
          const newSelectedNode = nodesSnapshot.find(n => n.id === selectedChange.id);
          if (newSelectedNode) {
            // Update selected node state
            setSelectedNode(newSelectedNode);
            
            const currentViewport = getViewport();
            
            // Center the selected node in the right half of the window
            const windowWidth = window.innerWidth;
            const windowHeight = window.innerHeight;
            
            // Get node dimensions (from node data or defaults)
            const nodeWidth = newSelectedNode.data?.width || 160;
            const nodeHeight = 80; // Approximate height based on typical node content
            
            // Center the node in the viewport
            const targetScreenX = windowWidth / 2;
            const targetScreenY = windowHeight / 2;
            
            // Calculate the node's center position (position is top-left corner)
            const nodeCenterX = newSelectedNode.position.x + nodeWidth / 2;
            const nodeCenterY = newSelectedNode.position.y + nodeHeight / 2;
            
            // Calculate required viewport position
            // Formula in React Flow: screenPos = worldPos * zoom + viewportPos
            // Therefore: viewportPos = screenPos - (worldPos * zoom)
            const newViewportX = targetScreenX - (nodeCenterX * currentViewport.zoom);
            const newViewportY = targetScreenY - (nodeCenterY * currentViewport.zoom);
            
            
            // Apply the viewport change with smooth easing animation
            setViewport(
              { x: newViewportX, y: newViewportY, zoom: currentViewport.zoom },
              { duration: 500, easing: (t) => t * (2 - t) } // ease-out quad for smooth deceleration
            );
          }
        } else {
          // Check for deselection (all nodes deselected)
          const hasDeselect = selectChanges.some(c => !c.selected);
          const allDeselected = !nodesSnapshot.some(n => n.selected);
          if (hasDeselect && allDeselected) {
            setSelectedNode(null);
          }
        }
        
        // Heuristic: If we get many deselect changes at once (typical when drag starts),
        // and we have selected nodes, it's likely a drag operation starting
        const isDragStarting = deselectChanges.length > 10 && nodesSnapshot.some(n => n.selected);
        
        // It's a drag operation if:
        // 1. draggingNodeId is already set, OR
        // 2. We have position + select changes together, OR
        // 3. We detect drag starting heuristic
        const isDragOperation = draggingNodeId || (hasPositionChanges && selectChanges.length > 0) || isDragStarting;
        
        if (isDragOperation) {
          // Filter out all selection changes during drag to preserve selection state
          filteredChanges = changes.filter((change) => change.type !== 'select');
        } else {
          // Not dragging - handle normal selection
          if (selectChanges.length > 0) {
            const selectChange = selectChanges.find(c => c.selected);
            if (selectChange) {
              // Add deselect changes for all other nodes to ensure single selection
              const deselectOthers = nodesSnapshot
                .filter(n => n.id !== selectChange.id && n.selected)
                .map(n => ({ id: n.id, type: 'select', selected: false }));
              filteredChanges = [...changes, ...deselectOthers];
            }
          }
        }
        
        const updatedNodes = applyNodeChanges(filteredChanges, nodesSnapshot);
        
        // Update edge positions when nodes move
        setEdges((edgesSnapshot) => updateEdgePositions(updatedNodes, edgesSnapshot));
        
        return updatedNodes;
      });
    },
    [updateEdgePositions, draggingNodeId],
  );
  const onEdgesChange = useCallback(
    (changes) => setEdges((edgesSnapshot) => applyEdgeChanges(changes, edgesSnapshot)),
    [],
  );
  const onConnect = useCallback(
    (params) => setEdges((edgesSnapshot) => addEdge(params, edgesSnapshot)),
    [],
  );

  // Track when dragging starts
  const onNodeDragStart = useCallback((event, node) => {
    setDraggingNodeId(node.id);
  }, []);

  // Track when dragging stops
  const onNodeDragStop = useCallback(() => {
    setDraggingNodeId(null);
  }, []);


  // Layout button handlers
  const handleColaLayout = useCallback(() => {
    applyColaPositions();
  }, [applyColaPositions]);

  const handleAvsdfLayout = useCallback(() => {
    applyAvsdfPositions();
  }, [applyAvsdfPositions]);

  const handleFcoseLayout = useCallback(() => {
    applyFcosePositions();
  }, [applyFcosePositions]);

  const handleRandomLayout = useCallback(() => {
    randomizePositions();
  }, [randomizePositions]);

  return (
    <div>
      <div>
        <div>
          <h1>Music Knowledge Graph</h1>
          {nodes.length > 0 && (
            <span >
              {nodes.length} entities • {edges.length} relationships
            </span>
          )}
        </div>
        {nodes.length > 0 && (
          <div>
            <Button onClick={handleFcoseLayout} variant="default" disabled={isAnimating}>
              ⚡ {isAnimating ? 'Animating...' : 'fCoSE Layout'}
            </Button>
            <Button onClick={handleColaLayout} variant="default" disabled={isAnimating}>
              🌐 {isAnimating ? 'Animating...' : 'Cola Layout'}
            </Button>
            <Button onClick={handleAvsdfLayout} variant="default" disabled={isAnimating}>
              🔄 {isAnimating ? 'Animating...' : 'AVSDF Layout'}
            </Button>
            <Button onClick={handleRandomLayout} variant="secondary" disabled={isAnimating}>
              🎲 {isAnimating ? 'Animating...' : 'Randomize Layout'}
            </Button>
          </div>
        )}
      </div>
      <div style={{ height: '100vh', width: `${width}vw` }}>
        <ReactFlow 
          nodes={nodes}
          edges={edges}
          nodeTypes={{ custom: CustomNode }}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDragStart={onNodeDragStart}
          onNodeDragStop={onNodeDragStop}
          selectNodesOnDrag={false}
          fitView
          attributionPosition="bottom-left"
          proOptions={{ hideAttribution: true }}
        />
      </div>
      <div>
        <span>👤 Musician</span>
        <span>👥 Collaborators</span>
        <span>🎸 Bands</span>
        <span>🎵 Songs</span>
        <span>🎹 Instruments</span>
        <span>🎼 Genres</span>
      </div>
    </div>
  );
}


  