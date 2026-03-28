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
import { BreadcrumbNode } from "./components/BreadcrumbNode";
import { SolidEdge } from "./components/CustomEdge";
import { CustomNode } from "./components/CustomNode";
import {
  breadcrumbsAtom,
  centerNodeAtom,
  draggingNodeIdAtom,
  edgesAtom,
  layoutNodesAtom,
  nodesAtom,
  selectedNodeAtom,
} from "./data/atoms";
import { sendNodeSelection } from "./data/api";
import {
  buildBridgeEdge,
  buildBreadcrumbRenderGraph,
} from "./lib/breadcrumbLayout";
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

function applyActiveNodeStyling(nodes, activeNodeId) {
  return nodes.map((node) => {
    const isActive = node.id === String(activeNodeId);

    return {
      ...node,
      data: {
        ...node.data,
        background: isActive ? "#038061" : "#ffffff",
        color: isActive ? "#ffffff" : "#038061",
      },
      selected: isActive,
    };
  });
}

export default function Graph({ data, width }) {
  const [nodes, setNodes] = useAtom(nodesAtom);
  const [edges, setEdges] = useAtom(edgesAtom);
  const [, setDraggingNodeId] = useAtom(draggingNodeIdAtom);
  const [selectedNode, setSelectedNode] = useAtom(selectedNodeAtom);
  const [centerNodeId, setCenterNodeId] = useAtom(centerNodeAtom);
  const [layoutNodes, setLayoutNodes] = useAtom(layoutNodesAtom);
  const [breadcrumbs, setBreadcrumbs] = useAtom(breadcrumbsAtom);

  const { getViewport, setViewport, fitView } = useReactFlow();
  const containerRef = useRef(null);
  const graphNodesRef = useRef([]);
  const edgesRef = useRef([]);
  const latestForwardNodeIdRef = useRef(null);
  const breadcrumbsCounter = useRef(0);

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

  const mergeAndSetRenderGraph = useCallback(() => {
    const viewport = getViewport();
    const containerWidth = containerRef.current?.clientWidth ?? 800;
    const { nodes: breadcrumbNodes, edges: breadcrumbEdges } =
      buildBreadcrumbRenderGraph(breadcrumbs, viewport, containerWidth);
    const anchorNodeId = latestForwardNodeIdRef.current ?? centerNodeId;
    const hasAnchorNode = graphNodesRef.current.some(
      (node) => node.id === String(anchorNodeId)
    );
    const bridgeEdge = hasAnchorNode
      ? buildBridgeEdge(breadcrumbs, anchorNodeId)
      : null;

    const nextNodes = [...graphNodesRef.current, ...breadcrumbNodes];
    const nextEdges = [
      ...edgesRef.current,
      ...breadcrumbEdges,
      ...(bridgeEdge ? [bridgeEdge] : []),
    ];

    setNodes((currentNodes) =>
      areNodeArraysEqual(currentNodes, nextNodes) ? currentNodes : nextNodes
    );
    setEdges((currentEdges) =>
      areEdgeArraysEqual(currentEdges, nextEdges) ? currentEdges : nextEdges
    );
  }, [breadcrumbs, centerNodeId, getViewport, setEdges, setNodes]);

  const appendBreadcrumb = useCallback(
    (node) => {
      let appended = false;

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

        appended = true;
        const entry = {
          historyId: `bc-${breadcrumbsCounter.current}`,
          originNodeId: node.id,
          label: node.data.label,
        };

        breadcrumbsCounter.current += 1;
        return [...prev, entry];
      });

      if (appended || latestForwardNodeIdRef.current == null) {
        latestForwardNodeIdRef.current = node.id;
      }
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
    const styledNodes = applyActiveNodeStyling(
      mergedNodes,
      selectedNode?.id ?? centerNodeId
    );

    setLayoutNodes((currentLayoutNodes) =>
      areNodeArraysEqual(currentLayoutNodes, styledNodes)
        ? currentLayoutNodes
        : styledNodes
    );
    graphNodesRef.current = styledNodes;
    edgesRef.current = newEdges;

    if (latestForwardNodeIdRef.current == null) {
      latestForwardNodeIdRef.current =
        selectedNode?.id || styledNodes[0]?.id || null;
    }

    mergeAndSetRenderGraph();

    if (!selectedNode) {
      const nodeToCenter = styledNodes.find((node) => node.id === "1");

      if (nodeToCenter && containerRef.current) {
        centerNodeInView(nodeToCenter);
        setSelectedNode(nodeToCenter);
      }
    }
  }, [
    centerNodeInView,
    data,
    layoutNodes,
    mergeAndSetRenderGraph,
    selectedNode,
    setLayoutNodes,
    setSelectedNode,
  ]);

  useEffect(() => {
    prepareGraphData();
  }, [prepareGraphData]);

  const onNodesChange = useCallback(
    (changes) => {
      const realChanges = changes.filter(
        (change) => !change.id?.startsWith("bc-")
      );

      setNodes((currentNodes) => {
        const updatedNodes = applyNodeChanges(changes, currentNodes);

        if (realChanges.length === 0) {
          return updatedNodes;
        }

        const realNodes = updatedNodes.filter(
          (node) => !node.id.startsWith("bc-")
        );
        const styledNodes = applyActiveNodeStyling(
          realNodes,
          selectedNode?.id ?? centerNodeId
        );

        graphNodesRef.current = styledNodes;
        edgesRef.current = updateEdges(styledNodes, edgesRef.current);

        const viewport = getViewport();
        const containerWidth = containerRef.current?.clientWidth ?? 800;
        const { edges: breadcrumbEdges } = buildBreadcrumbRenderGraph(
          breadcrumbs,
          viewport,
          containerWidth
        );
        const anchorNodeId = latestForwardNodeIdRef.current ?? centerNodeId;
        const hasAnchorNode = realNodes.some(
          (node) => node.id === String(anchorNodeId)
        );
        const bridgeEdge = hasAnchorNode
          ? buildBridgeEdge(breadcrumbs, anchorNodeId)
          : null;

        const nextEdges = [
          ...edgesRef.current,
          ...breadcrumbEdges,
          ...(bridgeEdge ? [bridgeEdge] : []),
        ];

        setEdges((currentEdges) =>
          areEdgeArraysEqual(currentEdges, nextEdges) ? currentEdges : nextEdges
        );

        return [
          ...styledNodes,
          ...updatedNodes.filter((node) => node.id.startsWith("bc-")),
        ];
      });
    },
    [
      breadcrumbs,
      centerNodeId,
      getViewport,
      selectedNode?.id,
      setEdges,
      setNodes,
      updateEdges,
    ]
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
      if (node.id.startsWith("bc-")) {
        const realNode = graphNodesRef.current.find(
          (graphNode) => graphNode.id === node.data.originNodeId
        );

        if (!realNode) {
          return;
        }

        setBreadcrumbs((prev) => {
          const clickedIndex = prev.findIndex(
            (entry) => entry.historyId === node.id
          );

          if (clickedIndex < 0) {
            return prev;
          }

          return prev.slice(0, clickedIndex + 1);
        });
        latestForwardNodeIdRef.current = node.data.originNodeId;
        setCenterNodeId(Number(node.data.originNodeId));
        setSelectedNode(realNode);
        centerNodeInView(realNode);
        sendNodeSelection(node.data.originNodeId);
        return;
      }

      latestForwardNodeIdRef.current = node.id;
      setCenterNodeId(Number(node.id));
      setSelectedNode(node);
      centerNodeInView(node);
      sendNodeSelection(node.id);
      appendBreadcrumb(node);
    },
    [
      appendBreadcrumb,
      centerNodeInView,
      setBreadcrumbs,
      setCenterNodeId,
      setSelectedNode,
    ]
  );

  const onNodeDragStart = useCallback(
    (_, node) => setDraggingNodeId(node.id),
    [setDraggingNodeId]
  );

  const onNodeDragStop = useCallback(
    () => setDraggingNodeId(null),
    [setDraggingNodeId]
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
      mergeAndSetRenderGraph();
    });

    ro.observe(container);

    return () => ro.disconnect();
  }, [fitView, mergeAndSetRenderGraph]);

  return (
    <div ref={containerRef} style={{ height: "100vh", width: `${width}vw` }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={{ custom: CustomNode, breadcrumb: BreadcrumbNode }}
        edgeTypes={{ solid: SolidEdge }}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeDragStart={onNodeDragStart}
        onNodeDragStop={onNodeDragStop}
        onNodeClick={onNodeClick}
        onMoveEnd={mergeAndSetRenderGraph}
        selectNodesOnDrag={false}
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
