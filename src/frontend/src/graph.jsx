import { useCallback, useEffect, useRef } from "react";
import {
  ReactFlow,
  applyEdgeChanges,
  addEdge,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { CustomNode } from "./components/CustomNode";
import {  getEdgeHandles } from "./lib/graphUtils";
import { useAtom } from "jotai";
import {
  nodesAtom,
  edgesAtom,
  draggingNodeIdAtom,
  selectedNodeAtom,
} from "./data/atoms";
import { applyNodeChanges } from "@xyflow/react";
import { calculateNodeDistances } from "./lib/graphUtils";
import { applyColaLayout } from "./lib/ctrytoscapeLayout";
import { sendNodeSelection } from "./data/api";

export default function Graph({ data, width }) {
  const [nodes, setNodes] = useAtom(nodesAtom);
  const [edges, setEdges] = useAtom(edgesAtom);
  const [draggingNodeId, setDraggingNodeId] = useAtom(draggingNodeIdAtom);
  const [selectedNode, setSelectedNode] = useAtom(selectedNodeAtom);
  const { setViewport, getViewport, fitView } = useReactFlow();
  const containerRef = useRef(null);
  // Convert knowledge graph data to React Flow nodes and edges
  useEffect(() => {
    if (!data || !data.allNodes || !data.allEdges) return;

    const newNodes = [];
    const newEdges = [];

    // Create nodes from all entities with placeholder positioning
    const nodeMap = new Map();
    data.allNodes.forEach((node) => {
      const centerNodeId = 1;
      const isCenter = node.id === centerNodeId;

      const reactFlowNode = {
        id: String(node.id),
        type: "custom",
        position: { x: 0, y: 0 }, // Placeholder - will be set by fCoSE
        data: {
          label: `${node.title}\n${
            node.released !== "N/A" ? `(${node.released})` : ""
          }`,
          background:  isCenter ? "#038061" : "#ffffff",
          color: isCenter ? "#ffffff" : "#038061",
          border: `2px solid #038061`,
          borderRadius: "8px",
          padding: "8px",
          fontSize: "12px",
          width: 160,
          whiteSpace: "pre-wrap",
          boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
        },
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
          type: "default",
          animated: false,
          sourceHandle,
          targetHandle,
          markerEnd: {
            type: "arrowclosed",
            color: "#999",
          },
          style: { stroke: "#999", strokeWidth: 1.5 },
          labelStyle: {
            fill: "#666",
            fontSize: "10px",
            fontWeight: "normal",
          },
          labelBgStyle: { fill: "white", fillOpacity: 0.8 },
        };
        newEdges.push(reactFlowEdge);
      }
    });

    // Apply fCoSE layout to get initial positions
    const fcosePositions = applyColaLayout(newNodes, newEdges, 1, {
      quality: "proof",
      nodeSeparation: 200,
      idealEdgeLength: 300,
      nodeRepulsion: 50000,
      gravity: 0.05,
      gravityRange: 5.0,
      numIter: 5000,
      initialEnergyOnIncremental: 0.3,
      tile: true,
      tilingPaddingVertical: 20,
      tilingPaddingHorizontal: 20,
    }, {x: containerRef.current.clientWidth, y: containerRef.current.clientHeight});

    // Apply fCoSE positions to nodes
    const nodesWithPositions = newNodes.map((node) => ({
      ...node,
      position: fcosePositions[node.id] || node.position,
    }));

    // Update React Flow state with positioned nodes
    setNodes(nodesWithPositions);
    setEdges(newEdges);


    const nodeToSelect = newNodes.find(n => n.id === "1");
  if (!nodeToSelect) return;

  const container = containerRef.current;
  if (!container) return;

  const containerWidth = container.clientWidth;
  const containerHeight = container.clientHeight;

  const nodeWidth = nodeToSelect.data?.width || 160;
  const nodeHeight = 80;

  const nodeCenterX = nodeToSelect.position.x + nodeWidth / 2;
  const nodeCenterY = nodeToSelect.position.y + nodeHeight / 2;

  setViewport(
    {
      x: containerWidth / 2 - nodeCenterX ,
      y: containerHeight / 2 - nodeCenterY,
    },
    { duration: 500, easing: t => t * (2 - t) }
  );

  setSelectedNode(nodeToSelect);

  // Optionally update distances and edges like your other selection logic
  const distances = calculateNodeDistances(nodeToSelect.id, newNodes, newEdges);
  setNodes(currentNodes =>
    currentNodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        distance: distances.get(node.id) ?? Infinity,
      },
    }))
  );
  setEdges(currentEdges =>
    currentEdges.map(edge => {
      const sourceDistance = distances.get(edge.source) ?? Infinity;
      const targetDistance = distances.get(edge.target) ?? Infinity;

      const isConnected = sourceDistance === 0 || targetDistance === 0;
      const bothDistant = sourceDistance > 1 && targetDistance > 1;

      return {
        ...edge,
        animated: isConnected,
        style: {
          ...edge.style,
          stroke: isConnected ? "#1a73e8" : bothDistant ? "var(--distant-edge-color)" : "#999",
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
    })
  );
  }, [data]);

  

  // Function to update edge handles based on node positions
  const updateEdgePositions = useCallback((currentNodes, currentEdges) => {
    // Create a map for quick node lookup
    const nodeMap = new Map(currentNodes.map((n) => [n.id, n]));

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

      return {
        ...edge,
        sourceHandle,
        targetHandle,
      };
    });
  }, []);

  useEffect(() => {
    // fit the view once on mount
    fitView({ padding: 0.1, duration: 200 });
  }, [fitView]);

  // Update node and edge styling based on selection
  useEffect(() => {
    if (selectedNode) {
      // Calculate distances from selected node
      const distances = calculateNodeDistances(selectedNode.id, nodes, edges);

      // Track which nodes will change their scale (for updateNodeInternals)
      const nodesNeedingUpdate = new Set();

      // Update nodes with distance information only (no width changes)
      setNodes((currentNodes) => {
        const updatedNodes = currentNodes.map((node) => {
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
        setEdges((currentEdges) => {
          return currentEdges.map((edge) => {
            const sourceDistance = distances.get(edge.source) ?? Infinity;
            const targetDistance = distances.get(edge.target) ?? Infinity;

            // Edge is connected if it connects to the selected node (distance 0)
            const isConnected = sourceDistance === 0 || targetDistance === 0;

            // Both nodes are distant (distance > 1)
            const bothDistant = sourceDistance > 1 && targetDistance > 1;

            // Determine edge color
            let strokeColor = "#999"; // default gray
            if (isConnected) {
              strokeColor = "#1a73e8"; // blue for connected
            } else if (bothDistant) {
              strokeColor = "var(--distant-edge-color)"; // persimmon/tomato for distant
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

        return updatedNodes;
      });
    } else {
      // Track which nodes were selected (for updateNodeInternals)
      const nodesNeedingUpdate = new Set();

      // Reset all nodes to remove distance data
      setNodes((currentNodes) => {
        const resetNodes = currentNodes.map((node) => {
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
        setEdges((currentEdges) => {
          return currentEdges.map((edge) => ({
            ...edge,
            animated: false,
            style: {
              stroke: "#999",
              strokeWidth: 1.5,
            },
            labelStyle: {
              fill: "#666",
              fontSize: "10px",
              fontWeight: "normal",
              opacity: 1,
            },
            labelBgStyle: {
              fill: "white",
              fillOpacity: 0.8,
            },
          }));
        });

        return resetNodes;
      });
    }
  }, [selectedNode, updateEdgePositions]);

  // Use the custom animation hook

  const onNodesChange = useCallback(
    (changes) => {
      setNodes((nodesSnapshot) => {
        let filteredChanges = changes;

        // Check change types in this batch
        const hasPositionChanges = changes.some(
          (change) => change.type === "position"
        );
        const selectChanges = changes.filter(
          (change) => change.type === "select"
        );
        const deselectChanges = selectChanges.filter((c) => !c.selected);

        // Detect node selection
        const selectedChange = selectChanges.find((c) => c.selected);
        if (selectedChange) {
          const newSelectedNode = nodesSnapshot.find(
            (n) => n.id === selectedChange.id
          );
          if (newSelectedNode) {
            // Update selected node state
            setSelectedNode(newSelectedNode);
            
            // Notify backend of node selection
            sendNodeSelection(newSelectedNode.id).then((context) => {
              if (context) {
                console.log("Node context:", context);
              }
            });

            const currentViewport = getViewport();

            const container = containerRef.current;
            if (!container) return;

            const containerWidth = container.clientWidth;
            const containerHeight = container.clientHeight;

            // Get node dimensions (from node data or defaults)
            const nodeWidth = newSelectedNode.data?.width || 160;
            const nodeHeight = 80; // Approximate height based on typical node content

            // Center the node in the viewport
            const targetScreenX = containerWidth / 2;
            const targetScreenY = containerHeight / 2;

            // Calculate the node's center position (position is top-left corner)
            const nodeCenterX = newSelectedNode.position.x + nodeWidth / 2;
            const nodeCenterY = newSelectedNode.position.y + nodeHeight / 2;

            // Calculate required viewport position
            // Formula in React Flow: screenPos = worldPos * zoom + viewportPos
            // Therefore: viewportPos = screenPos - (worldPos * zoom)
            const newViewportX =
              targetScreenX - nodeCenterX * currentViewport.zoom;
            const newViewportY =
              targetScreenY - nodeCenterY * currentViewport.zoom;

            // Apply the viewport change with smooth easing animation
            setViewport(
              { x: newViewportX, y: newViewportY, zoom: currentViewport.zoom },
              { duration: 500, easing: (t) => t * (2 - t) } // ease-out quad for smooth deceleration
            );
          }
        } else {
          // Check for deselection (all nodes deselected)
          const hasDeselect = selectChanges.some((c) => !c.selected);
          const allDeselected = !nodesSnapshot.some((n) => n.selected);
          if (hasDeselect && allDeselected) {
            setSelectedNode(null);
          }
        }

        // Heuristic: If we get many deselect changes at once (typical when drag starts),
        // and we have selected nodes, it's likely a drag operation starting
        const isDragStarting =
          deselectChanges.length > 10 && nodesSnapshot.some((n) => n.selected);

        // It's a drag operation if:
        // 1. draggingNodeId is already set, OR
        // 2. We have position + select changes together, OR
        // 3. We detect drag starting heuristic
        const isDragOperation =
          draggingNodeId ||
          (hasPositionChanges && selectChanges.length > 0) ||
          isDragStarting;

        if (isDragOperation) {
          // Filter out all selection changes during drag to preserve selection state
          filteredChanges = changes.filter(
            (change) => change.type !== "select"
          );
        } else {
          // Not dragging - handle normal selection
          if (selectChanges.length > 0) {
            const selectChange = selectChanges.find((c) => c.selected);
            if (selectChange) {
              // Add deselect changes for all other nodes to ensure single selection
              const deselectOthers = nodesSnapshot
                .filter((n) => n.id !== selectChange.id && n.selected)
                .map((n) => ({ id: n.id, type: "select", selected: false }));
              filteredChanges = [...changes, ...deselectOthers];
            }
          }
        }

        const updatedNodes = applyNodeChanges(filteredChanges, nodesSnapshot);

        // Update edge positions when nodes move
        setEdges((edgesSnapshot) =>
          updateEdgePositions(updatedNodes, edgesSnapshot)
        );

        return updatedNodes;
      });
    },
    [updateEdgePositions, draggingNodeId]
  );
  const onEdgesChange = useCallback(
    (changes) =>
      setEdges((edgesSnapshot) => applyEdgeChanges(changes, edgesSnapshot)),
    []
  );
  const onConnect = useCallback(
    (params) => setEdges((edgesSnapshot) => addEdge(params, edgesSnapshot)),
    []
  );

  // Track when dragging starts
  const onNodeDragStart = useCallback((event, node) => {
    setDraggingNodeId(node.id);
  }, []);

  // Track when dragging stops
  const onNodeDragStop = useCallback(() => {
    setDraggingNodeId(null);
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const ro = new ResizeObserver(() => {
      fitView({ padding: 0.1, duration: 150 }); // recalc viewport when container size changes
    });

    ro.observe(el);
    return () => ro.disconnect();
  }, [fitView, width]);


  const getVisibleNodesAndEdges = (allNodes, allEdges, selectedNode) => {
  if (!selectedNode) {
    // If no node is selected, show all
    return { nodes: allNodes, edges: allEdges };
  }


  // Find all nodes connected to the selected node
  const connectedNodeIds = new Set([selectedNode.id]);
  allEdges.forEach(edge => {
    if (edge.source === selectedNode.id) connectedNodeIds.add(edge.target);
    if (edge.target === selectedNode.id) connectedNodeIds.add(edge.source);
  });

  // Filter nodes
  const nodes = allNodes.filter(n => connectedNodeIds.has(n.id));

  // Filter edges
  const edges = allEdges.filter(
    e =>
      connectedNodeIds.has(e.source) &&
      connectedNodeIds.has(e.target)
  );

  return { nodes, edges };
};



const { nodes: visibleNodes, edges: visibleEdges } = getVisibleNodesAndEdges(
  nodes,
  edges,
  selectedNode
);

  return (
    <div>
      <div>
      </div>
      <div ref={containerRef} style={{ height: "100vh", width: { width } }}>
        <ReactFlow
          nodes={visibleNodes}
          edges={visibleEdges}
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
    </div>
  );
}
