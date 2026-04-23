import { useCallback, useEffect, useRef } from "react";
import {
  ReactFlow,
  applyEdgeChanges,
  addEdge,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { CustomNode } from "./components/CustomNode";
import { SolidEdge } from "./components/CustomEdge";
import { getEdgeHandles } from "./lib/graphUtils";
import { applyDagreLayout } from "./lib/ctrytoscapeLayout";
import { useAtom } from "jotai";
import {
  nodesAtom,
  edgesAtom,
  selectedNodeAtom,
  centerNodeAtom,
  layoutNodesAtom,
} from "./data/atoms";
import { sendNodeSelection } from "./data/api";

export default function Graph({ data, width }) {
  const [nodes, setNodes] = useAtom(nodesAtom);
  const [edges, setEdges] = useAtom(edgesAtom);
  const [selectedNode, setSelectedNode] = useAtom(selectedNodeAtom);
  const [, setCenterNodeId] = useAtom(centerNodeAtom);
  const [layoutNodes, setLayoutNodes] = useAtom(layoutNodesAtom);

  const { getViewport, setViewport, fitView } = useReactFlow();
  const containerRef = useRef(null);
  const nodesRef = useRef([]);
  const edgesRef = useRef([]);

  /** Convert raw data to React Flow nodes & edges */
  const prepareGraphData = useCallback(() => {
    if (!data?.nodes || !data?.edges) return;

    const previousPositions = new Map(
      layoutNodes.map((n) => [n.id, n.position]),
    );
    const nodeMap = new Map();

    // Create nodes
    const newNodes = data.nodes.map((node) => {
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
    const newEdges = data.edges
      .map((edge) => {
        const sourceNode = nodeMap.get(String(edge.source_id));
        const targetNode = nodeMap.get(String(edge.target_id));
        if (!sourceNode || !targetNode) return null;

        const { sourceHandle, targetHandle } = getEdgeHandles(
          sourceNode.position.x,
          sourceNode.position.y,
          targetNode.position.x,
          targetNode.position.y,
        );

        return {
          id: String(edge.id),
          source: String(edge.source_id),
          target: String(edge.target_id),
          label: edge.label_forward,
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
    // Merge positions: keep old positions, use fcose positions for new
    const mergedNodes = newNodes.map((n) => ({
      ...n,
      position:
        previousPositions.get(n.id) || layoutPositions[n.id] || n.position,
    }));

    setLayoutNodes(mergedNodes);
    nodesRef.current = mergedNodes;
    edgesRef.current = newEdges;

    setNodes(mergedNodes);
    setEdges(newEdges);

    // Center initial node if none selected
    if (!selectedNode) {
      const nodeToCenter = mergedNodes.find((n) => n.id === "1");
      if (nodeToCenter && containerRef.current) {
        centerNodeInView(nodeToCenter);
        setSelectedNode(nodeToCenter);
      }
    }
  }, [data]);

  useEffect(() => {
    prepareGraphData();
  }, [prepareGraphData]);

  /** Update edge handles when nodes move */
  const updateEdges = useCallback((nodes, edges) => {
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    return edges.map((edge) => {
      const sourceNode = nodeMap.get(edge.source);
      const targetNode = nodeMap.get(edge.target);
      if (!sourceNode || !targetNode) return edge;

      const { sourceHandle, targetHandle } = getEdgeHandles(
        sourceNode.position.x,
        sourceNode.position.y,
        targetNode.position.x,
        targetNode.position.y,
        160,
        80,
      );

      return { ...edge, sourceHandle, targetHandle };
    });
  }, []);

  const onEdgesChange = useCallback(
    (changes) =>
      setEdges((currentEdges) => applyEdgeChanges(changes, currentEdges)),
    [setEdges],
  );

  const onConnect = useCallback(
    (params) => setEdges((es) => addEdge(params, es)),
    [setEdges],
  );

  const onNodeClick = useCallback(
    (_, node) => {
      setCenterNodeId(Number(node.id));
      setSelectedNode(node);
      centerNodeInView(node);
      sendNodeSelection(node.id);
    },
    [setCenterNodeId, setSelectedNode],
  );

  /** Center a node in the viewport */
  const centerNodeInView = useCallback(
    (node) => {
      if (!containerRef.current) return;
      const { width: nodeWidth = 160, height: nodeHeight = 80 } =
        node.data || {};
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
        { duration: 500, easing: (t) => t * (2 - t) },
      );
    },
    [getViewport, setViewport],
  );

  /** Fit view on container resize */
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const ro = new ResizeObserver(() =>
      fitView({ padding: 0.1, duration: 150 }),
    );
    ro.observe(container);
    return () => ro.disconnect();
  }, [fitView]);

  return (
    <div ref={containerRef} style={{ height: "100vh", width: `${width}vw` }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={{ custom: CustomNode }}
        edgeTypes={{ solid: SolidEdge }}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        selectNodesOnDrag={false}
        fitView
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
      />
    </div>
  );
}
