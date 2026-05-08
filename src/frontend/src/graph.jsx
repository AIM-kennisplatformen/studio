import { useCallback, useEffect, useRef } from "react";
import {
  ReactFlow,
  applyEdgeChanges,
  addEdge,
  applyNodeChanges,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useAtom } from "jotai";
import { SolidEdge } from "./components/CustomEdge";
import { CustomNode } from "./components/CustomNode";
import {
  breadcrumbsAtom,
  centerNodeAtom,
  edgesAtom,
  layoutNodesAtom,
  nodesAtom,
  selectedNodeAtom,
  selectedNodeScreenPositionAtom,
} from "./data/atoms";
import { sendNodeSelection } from "./data/api";
import { applyDagreLayout } from "./lib/ctrytoscapeLayout";
import { getEdgeHandles } from "./lib/graphUtils";

function arePositionsEqual(a = { x: 0, y: 0 }, b = { x: 0, y: 0 }) {
  return a.x === b.x && a.y === b.y;
}

function areNodeArraysEqual(currentNodes, nextNodes) {
  if (currentNodes.length !== nextNodes.length) {
    return false;
  }

  return currentNodes.every((node, index) => {
    const nextNode = nextNodes[index];

    return (
      node.id === nextNode.id &&
      node.type === nextNode.type &&
      node.draggable === nextNode.draggable &&
      node.selectable === nextNode.selectable &&
      node.connectable === nextNode.connectable &&
      arePositionsEqual(node.position, nextNode.position) &&
      JSON.stringify(node.data) === JSON.stringify(nextNode.data)
    );
  });
}

function areEdgeArraysEqual(currentEdges, nextEdges) {
  if (currentEdges.length !== nextEdges.length) {
    return false;
  }

  return currentEdges.every((edge, index) => {
    const nextEdge = nextEdges[index];

    return (
      edge.id === nextEdge.id &&
      edge.source === nextEdge.source &&
      edge.target === nextEdge.target &&
      edge.sourceHandle === nextEdge.sourceHandle &&
      edge.targetHandle === nextEdge.targetHandle &&
      JSON.stringify(edge.style || {}) === JSON.stringify(nextEdge.style || {})
    );
  });
}

export default function Graph({ data, width }) {
  const [nodes, setNodes] = useAtom(nodesAtom);
  const [edges, setEdges] = useAtom(edgesAtom);
  const [selectedNode, setSelectedNode] = useAtom(selectedNodeAtom);
  const [centerNodeId, setCenterNodeId] = useAtom(centerNodeAtom);
  const [layoutNodes, setLayoutNodes] = useAtom(layoutNodesAtom);
  const [, setBreadcrumbs] = useAtom(breadcrumbsAtom);

  const { getViewport, setViewport, fitView } = useReactFlow();
  const containerRef = useRef(null);
  const graphNodesRef = useRef([]);
  const edgesRef = useRef([]);
  const breadcrumbsCounter = useRef(0);

  const { flowToScreenPosition } = useReactFlow();
  const [, setSelectedNodeScreenPosition] = useAtom(
    selectedNodeScreenPositionAtom
  );

  // useEffect(() => {
  //   setSelectedNodeScreenPosition(screenPositionSelectedNode);
  // }, [screenPositionSelectedNode]);
  // console.log(selectedNode != null ? selectedNode.data.label : "niets");

  // console.log(screenPositionSelectedNode);

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
        { duration: 500, easing: (t) => t * (2 - t) }
      );
    },
    [getViewport, setViewport]
  );

  const setRenderGraph = useCallback(() => {
    const nextNodes = [...graphNodesRef.current];
    const nextEdges = [...edgesRef.current];

    setNodes((currentNodes) =>
      areNodeArraysEqual(currentNodes, nextNodes) ? currentNodes : nextNodes
    );
    setEdges((currentEdges) =>
      areEdgeArraysEqual(currentEdges, nextEdges) ? currentEdges : nextEdges
    );
  }, [setEdges, setNodes]);

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

  const updateEdges = useCallback((currentNodes, currentEdges) => {
    const nodeMap = new Map(currentNodes.map((node) => [node.id, node]));

    return currentEdges.map((edge) => {
      const sourceNode = nodeMap.get(edge.source);
      const targetNode = nodeMap.get(edge.target);

      if (!sourceNode || !targetNode) {
        return edge;
      }

      const { sourceHandle, targetHandle } = getEdgeHandles(
        sourceNode.position.x,
        sourceNode.position.y,
        targetNode.position.x,
        targetNode.position.y,
        160,
        80
      );

      return { ...edge, sourceHandle, targetHandle };
    });
  }, []);

  const prepareGraphData = useCallback(() => {
    if (!data?.nodes || !data?.edges) {
      return;
    }

    const previousPositions = new Map(
      layoutNodes.map((node) => [node.id, node.position])
    );
    const nodeMap = new Map();

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

    const newEdges = data.edges
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
          label: edge.label_forward,
          type: "solid",
          sourceHandle,
          targetHandle,
          labelStyle: { fill: "#666", fontSize: 10 },
          labelBgStyle: { fill: "white", fillOpacity: 0.8 },
        };
      })
      .filter(Boolean);

    const fixedNodes = newNodes.filter((node) =>
      previousPositions.has(node.id)
    );
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
      fixedNodeConstraint: fixedNodes.map((node) => ({
        nodeId: node.id,
        position: node.position,
      })),
    });

    const mergedNodes = newNodes.map((node) => ({
      ...node,
      position:
        previousPositions.get(node.id) ||
        layoutPositions[node.id] ||
        node.position,
    }));

    setLayoutNodes((currentLayoutNodes) =>
      areNodeArraysEqual(currentLayoutNodes, mergedNodes)
        ? currentLayoutNodes
        : mergedNodes
    );
    graphNodesRef.current = mergedNodes;
    edgesRef.current = newEdges;

    setRenderGraph();

    if (!selectedNode) {
      const nodeToCenter = mergedNodes.find((node) => node.id === "1");

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
  }, [
    centerNodeInView,
    data,
    layoutNodes,
    setRenderGraph,
    selectedNode,
    setLayoutNodes,
    setSelectedNode,
  ]);

  useEffect(() => {
    prepareGraphData();
  }, [prepareGraphData]);

  const onNodesChange = useCallback(
    (changes) => {
      setNodes((currentNodes) => {
        const updatedNodes = applyNodeChanges(changes, currentNodes);

        graphNodesRef.current = updatedNodes;
        edgesRef.current = updateEdges(updatedNodes, edgesRef.current);

        setEdges((currentEdges) =>
          areEdgeArraysEqual(currentEdges, edgesRef.current)
            ? currentEdges
            : edgesRef.current
        );

        return updatedNodes;
      });
    },
    [setEdges, setNodes, updateEdges]
  );

  const onEdgesChange = useCallback(
    (changes) =>
      setEdges((currentEdges) => applyEdgeChanges(changes, currentEdges)),
    [setEdges]
  );

  const onConnect = useCallback(
    (params) => setEdges((currentEdges) => addEdge(params, currentEdges)),
    [setEdges]
  );

  const onNodeClick = useCallback(
    (_, node) => {
      setCenterNodeId(Number(node.id));
      setSelectedNode(node);
      centerNodeInView(node);
      sendNodeSelection(node.id);
      appendBreadcrumb(node);

      const screenPositionSelectedNode = flowToScreenPosition(
        selectedNode != null ? selectedNode.position : { x: 0, y: 0 }
      );
      setSelectedNodeScreenPosition(screenPositionSelectedNode);
    },
    [appendBreadcrumb, centerNodeInView, setCenterNodeId, setSelectedNode]
  );

  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    const ro = new ResizeObserver(() => {
      fitView({
        padding: 0.1,
        duration: 150,
        nodes: graphNodesRef.current.map((n) => ({ id: n.id })),
      });
    });

    ro.observe(container);

    return () => ro.disconnect();
  }, [fitView]);

  return (
    <div
      ref={containerRef}
      style={{ height: "100vh", width: `${width}vw`, position: "relative" }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={{ custom: CustomNode }}
        edgeTypes={{ solid: SolidEdge }}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{
          padding: 0.5,
          duration: 150,
          nodes: graphNodesRef.current.map((n) => ({ id: n.id })),
        }}
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
      />
    </div>
  );
}
