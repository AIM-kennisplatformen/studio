import { useCallback, useEffect, useRef } from "react";
import {
  ReactFlow,
  applyEdgeChanges,
  addEdge,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useAtom, useAtomValue } from "jotai";
import { SolidEdge } from "./components/CustomEdge";
import { CustomNode } from "./components/CustomNode";
import { getEdgeHandles } from "./lib/graphUtils";
import { applyDagreLayout } from "./lib/ctrytoscapeLayout";
import {
  nodesAtom,
  edgesAtom,
  selectedNodeAtom,
  centerNodeAtom,
  layoutNodesAtom,
  breadcrumbsAtom,
  selectNodeEmitAtom,
  selectedNodeVerticalPositionAtom,
} from "./data/atoms";
import { sendNodeSelection } from "./data/api";

function getSubgraph(data, nodeId) {
  const id = String(nodeId);
  const connectedEdges = data.edges.filter(
    (e) => String(e.source_id) === id || String(e.target_id) === id
  );
  const neighborIds = new Set(
    connectedEdges.flatMap((e) => [String(e.source_id), String(e.target_id)])
  );
  return {
    nodes: data.nodes.filter((n) => neighborIds.has(String(n.id))),
    edges: connectedEdges,
  };
}

export default function Graph({ data }) {
  const [nodes, setNodes] = useAtom(nodesAtom);
  const [edges, setEdges] = useAtom(edgesAtom);
  const [selectedNode, setSelectedNode] = useAtom(selectedNodeAtom);
  const [centerNodeId, setCenterNodeId] = useAtom(centerNodeAtom);
  const [layoutNodes, setLayoutNodes] = useAtom(layoutNodesAtom);
  const [, setBreadcrumbs] = useAtom(breadcrumbsAtom);
  const emitSelectNode = useAtomValue(selectNodeEmitAtom);

  const { getViewport, setViewport, fitView } = useReactFlow();
  const containerRef = useRef(null);
  const edgesRef = useRef([]);
  const breadcrumbsCounter = useRef(0);

  const { flowToScreenPosition } = useReactFlow();
  const [, setSelectedNodeVerticalPosition] = useAtom(
    selectedNodeVerticalPositionAtom
  );
  const fullDataRef = useRef(null);
  const layoutNodesRef = useRef(layoutNodes);
  const selectedNodeRef = useRef(null);
  const allPositionsRef = useRef(new Map());

  const nodesRef = useRef([]);

  const centerNodeInView = useCallback(
    (node) => {
      if (!containerRef.current) return;

      const baseWidth = node.data?.width || 160;
      const baseHeight = 80;
      // Account for the scale applied to selected/center nodes
      const scale = 1.3;
      const nodeWidth = baseWidth * scale;
      const nodeHeight = baseHeight * scale;

      // node.position is the top-left of the wrapper; center of the visual node
      const nodeCenterX = node.position.x + nodeWidth / 2;
      const nodeCenterY = node.position.y + nodeHeight / 2;
      const viewport = getViewport();

      setViewport(
        {
          x: containerRef.current.clientWidth / 2 - nodeCenterX * viewport.zoom,
          y:
            containerRef.current.clientHeight / 2 - nodeCenterY * viewport.zoom,
          zoom: viewport.zoom,
        },
        { duration: 500, easing: (t) => t * (2 - t) }
      );
    },
    [getViewport, setViewport]
  );

  const appendBreadcrumb = useCallback(
    (node) => {
      setBreadcrumbs((prev) => {
        const lastEntry = prev[prev.length - 1];

        if (
          lastEntry?.originNodeId === node.id &&
          lastEntry?.label === node.data.label
        ) {
          return prev;
        }

        const existingIndex = prev.findIndex(
          (entry) => entry.originNodeId === node.id
        );

        if (existingIndex >= 0) {
          return prev.slice(0, existingIndex + 1);
        }

        const entry = {
          historyId: `bc-${breadcrumbsCounter.current}`,
          originNodeId: node.id,
          label: node.data.label,
        };

        breadcrumbsCounter.current += 1;
        return [...prev, entry];
      });
    },
    [setBreadcrumbs]
  );

  useEffect(() => {
    layoutNodesRef.current = layoutNodes;
  }, [layoutNodes]);

  useEffect(() => {
    selectedNodeRef.current = selectedNode;
  }, [selectedNode]);

  const prepareGraphData = useCallback(
    (graphData) => {
      if (!graphData?.nodes || !graphData?.edges) return;

      const previousPositions = allPositionsRef.current;
      const nodeMap = new Map();

      // Create nodes
      const newNodes = graphData.nodes.map((node) => {
        const isCenter = node.id === 1;
        const reactFlowNode = {
          id: String(node.id),
          type: "custom",
          position: previousPositions.get(String(node.id)) || { x: 0, y: 0 },
          data: {
            label: node.title,
            background: isCenter ? "#038061" : "#ffffff",
            color: isCenter ? "#ffffff" : "#038061",
            border: "2px solid #038061",
            borderRadius: "8px",
            padding: "8px",
            fontSize: "12px",
            width: 160,
            whiteSpace: "pre-wrap",
            boxShadow: "0 4px 8px rgba(0,0,0,0.1)",
          },
        };
        nodeMap.set(reactFlowNode.id, reactFlowNode);
        return reactFlowNode;
      });

      // Create edges
      const newEdges = graphData.edges
        .map((edge) => {
          const sourceNode = nodeMap.get(String(edge.source_id));
          const targetNode = nodeMap.get(String(edge.target_id));

          if (!sourceNode || !targetNode) {
            return null;
          }

          const { sourceHandle, targetHandle } = getEdgeHandles(
            sourceNode.position.x,
            sourceNode.position.y,
            targetNode.position.x,
            targetNode.position.y
          );

          return {
            id: String(edge.id),
            source: String(edge.source_id),
            target: String(edge.target_id),
            label: edge.labelToTarget,
            type: "solid",
            sourceHandle,
            targetHandle,
            labelStyle: { fill: "#666", fontSize: 10 },
            labelBgStyle: { fill: "white", fillOpacity: 0.8 },
          };
        })
        .filter(Boolean);

      const fixedNodes = newNodes.filter((n) => previousPositions.has(n.id));

      // Apply dagre layout to new nodes, keeping fixed nodes in place
      const layoutPositions = applyDagreLayout(newNodes, newEdges, {
        quality: "proof",
        nodeSeparation: 200,
        idealEdgeLength: 300,
        nodeRepulsion: 50000,
        maxIterations: 2000,
        animationDuration: 1000,
        gravity: 0.05,
        numIter: 5000,
        tile: true,
        tilingPaddingVertical: 20,
        tilingPaddingHorizontal: 20,
        incremental: true,
        nodeDimensionsIncludeLabels: true,
        fixedNodeConstraint: fixedNodes.map((n) => ({
          nodeId: n.id,
          position: n.position,
        })),
      });

      // Merge positions: keep old positions, use layout positions for new nodes
      const mergedNodes = newNodes.map((n) => ({
        ...n,
        position:
          previousPositions.get(n.id) || layoutPositions[n.id] || n.position,
      }));

      // Persist positions for all seen nodes across subgraph changes
      mergedNodes.forEach((n) => allPositionsRef.current.set(n.id, n.position));

      setLayoutNodes(mergedNodes);
      nodesRef.current = mergedNodes;
      edgesRef.current = newEdges;
      setNodes(mergedNodes);
      setEdges(newEdges);

      // Center node 1 on first load only
      if (!selectedNodeRef.current) {
        const nodeToCenter = mergedNodes.find((n) => n.id === "1");
        if (nodeToCenter && containerRef.current) {
          centerNodeInView(nodeToCenter);
          setSelectedNode(nodeToCenter);
          setBreadcrumbs(() => {
            const entry = {
              historyId: `bc-${breadcrumbsCounter.current}`,
              originNodeId: nodeToCenter.id,
              label: nodeToCenter.data.label,
            };

            breadcrumbsCounter.current += 1;
            return [entry];
          });
        }
      }
    },
    [
      setLayoutNodes,
      setNodes,
      setEdges,
      centerNodeInView,
      setSelectedNode,
      setBreadcrumbs,
    ]
  );

  // On first load show node 1's neighbourhood; on refetch just update fullDataRef
  useEffect(() => {
    if (!data) return;
    const isFirstLoad = fullDataRef.current === null;
    fullDataRef.current = data;
    if (isFirstLoad) prepareGraphData(getSubgraph(data, 1));
  }, [data, prepareGraphData]);

  const onEdgesChange = useCallback(
    (changes) =>
      setEdges((currentEdges) => applyEdgeChanges(changes, currentEdges)),
    [setEdges]
  );

  const onConnect = useCallback(
    (params) => setEdges((es) => addEdge(params, es)),
    [setEdges]
  );

  const onNodeClick = useCallback(
    (_, node) => {
      setCenterNodeId(Number(node.id));
      setSelectedNode(node);
      centerNodeInView(node);
      sendNodeSelection(node.id);
      appendBreadcrumb(node);

      emitSelectNode?.(Number(node.id));
      if (fullDataRef.current) {
        prepareGraphData(getSubgraph(fullDataRef.current, node.id));
      }
    },
    [
      setCenterNodeId,
      setSelectedNode,
      centerNodeInView,
      appendBreadcrumb,
      flowToScreenPosition,
      setSelectedNodeVerticalPosition,
      emitSelectNode,
      prepareGraphData,
    ]
  );

  /** Fit view on container resize — only when no node is selected (initial state) */

  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    let resizeTimer;
    const ro = new ResizeObserver(() => {
      // Debounce to avoid fighting with centerNodeInView animations
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        if (selectedNodeRef.current) {
          // Re-center the selected node after resize
          centerNodeInView(selectedNodeRef.current);
        } else {
          fitView({
            padding: 0.2,
            duration: 150,
          });
        }
      }, 200);
    });

    ro.observe(container);

    return () => {
      clearTimeout(resizeTimer);
      ro.disconnect();
    };
  }, [fitView, centerNodeInView]);

  useEffect(() => {
    const nodeIdStr = String(centerNodeId);
    const nodeToBeCentered = nodes.find((node) => node.id === nodeIdStr);

    if (nodeToBeCentered) {
      setSelectedNode(nodeToBeCentered);
      centerNodeInView(nodeToBeCentered);
      appendBreadcrumb(nodeToBeCentered);
      sendNodeSelection(nodeIdStr);
      emitSelectNode?.(Number(centerNodeId));

      if (fullDataRef.current) {
        prepareGraphData(getSubgraph(fullDataRef.current, centerNodeId));
      }
    }
  }, [centerNodeId]);

  return (
    <div
      ref={containerRef}
      style={{ height: "100%", width: "100%", position: "relative" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={{ custom: CustomNode }}
        edgeTypes={{ solid: SolidEdge }}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{
          padding: 0.2,
          duration: 150,
        }}
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
        onMove={() => {
          if (!selectedNode) return;
          // Calculate the vertical center of the selected node in screen coordinates
          // Center node: scale=1.3, base height≈80 → wrapperHeight=104, half=52
          const nodeHalfHeight = (80 * 1.3) / 2;
          const screenPositionCenter = flowToScreenPosition({
            x: selectedNode.position.x,
            y: selectedNode.position.y + nodeHalfHeight,
          });
          setSelectedNodeVerticalPosition(screenPositionCenter.y);
        }}
      />
    </div>
  );
}
