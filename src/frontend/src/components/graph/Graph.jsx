import { useCallback, useEffect, useRef } from "react";
import { ReactFlow, useReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { CustomNode } from "./nodes/CustomNode";
import { SolidEdge } from "./nodes/CustomEdge";
import { getEdgeHandles } from "./graphUtils";
import { applyDagreLayout, applyFcoseLayout } from "./layout/cytoscapeLayout";
import { useAtom, useAtomValue } from "jotai";
import {
  nodesAtom,
  edgesAtom,
  selectedNodeAtom,
  centerNodeAtom,
  layoutNodesAtom,
  selectNodeEmitAtom,
} from "../../lib/atoms";

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

export default function Graph({ data, width }) {
  const [nodes, setNodes] = useAtom(nodesAtom);
  const [edges, setEdges] = useAtom(edgesAtom);
  const [selectedNode, setSelectedNode] = useAtom(selectedNodeAtom);
  const [, setCenterNodeId] = useAtom(centerNodeAtom);
  const [layoutNodes, setLayoutNodes] = useAtom(layoutNodesAtom);
  const emitSelectNode = useAtomValue(selectNodeEmitAtom);

  const { getViewport, setViewport, fitView } = useReactFlow();
  const containerRef = useRef(null);
  const nodesRef = useRef([]);
  const edgesRef = useRef([]);
  const fullDataRef = useRef(null);
  const layoutNodesRef = useRef(layoutNodes);
  const selectedNodeRef = useRef(null);
  const allPositionsRef = useRef(new Map());

  useEffect(() => {
    layoutNodesRef.current = layoutNodes;
  }, [layoutNodes]);

  useEffect(() => {
    selectedNodeRef.current = selectedNode;
  }, [selectedNode]);

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
        { duration: 500, easing: (t) => t * (2 - t) }
      );
    },
    [getViewport, setViewport]
  );

  const prepareGraphData = useCallback(
    (graphData, centerId = 1) => {
      if (!graphData?.nodes || !graphData?.edges) return;

      const previousPositions = allPositionsRef.current;
      const nodeMap = new Map();

      // Create nodes
      const newNodes = graphData.nodes.map((node) => {
        const isCenter = node.id === centerId;
        const reactFlowNode = {
          id: String(node.id),
          type: "custom",
          position: previousPositions.get(String(node.id)) || { x: 0, y: 0 },
          data: {
            label: node.title,
            isFocused: isCenter,
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
          if (!sourceNode || !targetNode) return null;

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

      // const fixedNodes = newNodes.filter((n) => previousPositions.has(n.id));

      // Effe hardcoded of vanuit je state die andere constraints trekken:
      // 1. Define your source constraints (always use Strings for IDs)
      const fixedNodes = [{ id: "1", position: { x: 0, y: 0 } }];

      const alignmentConstraints = [
        { type: "horizontal", nodeIds: ["2", "3", "4"] },
      ];

      const relativePlacementConstraints = [
        { top: "1", bottom: "3", gap: 150 },
      ];

      // 2. Get a Set of all node IDs currently present in the graph
      const activeNodeIds = new Set(newNodes.map((node) => String(node.id)));

      // 3. Filter and map alignment IDs that are actually active
      const activeAlignedIds = ["2", "3", "4"].filter((id) =>
        activeNodeIds.has(id)
      );

      // 4. Run the fcose layout engine with correct configurations
      const layoutPositions = applyFcoseLayout(newNodes, newEdges, {
        quality: "proof",
        nodeSeparation: 200,
        idealEdgeLength: 300,
        nodeRepulsion: 50000,
        maxIterations: 3000,
        animationDuration: 1000,
        gravity: 0.05,
        numIter: 5000,
        nodeDimensionsIncludeLabels: true,

        // Disabling tile and incremental ensures constraints are strictly followed
        tile: false,
        incremental: false,

        // Map Fixed Constraints
        fixedNodeConstraint: fixedNodes
          .filter((node) => activeNodeIds.has(String(node.id)))
          .map((node) => ({
            nodeId: String(node.id),
            position: node.position,
          })),

        // Map Alignment Constraints directly into the expected library object format
        alignmentConstraint:
          activeAlignedIds.length >= 2
            ? {
                horizontal: [activeAlignedIds],
              }
            : undefined,

        // Map Relative Placement Constraints
        relativePlacementConstraint: relativePlacementConstraints
          .filter((constraint) => {
            const sourceId = constraint.left || constraint.top;
            const targetId = constraint.right || constraint.bottom;
            return (
              activeNodeIds.has(String(sourceId)) &&
              activeNodeIds.has(String(targetId))
            );
          })
          .map((constraint) => {
            if (constraint.left && constraint.right) {
              return {
                left: String(constraint.left),
                right: String(constraint.right),
                gap: Number(constraint.gap) || 20,
              };
            } else {
              return {
                top: String(constraint.top),
                bottom: String(constraint.bottom),
                gap: Number(constraint.gap) || 20,
              };
            }
          }),
      });
      // Apply dagre layout to new nodes, keeping fixed nodes in place
      // const layoutPositions = applyDagreLayout(newNodes, newEdges, {
      //   quality: "proof",
      //   nodeSeparation: 200,
      //   idealEdgeLength: 300,
      //   nodeRepulsion: 50000,
      //   maxIterations: 2000,
      //   animationDuration: 1000,
      //   gravity: 0.05,
      //   numIter: 5000,
      //   tile: false,
      //   tilingPaddingVertical: 20,
      //   tilingPaddingHorizontal: 20,
      //   incremental: true,
      //   nodeDimensionsIncludeLabels: true,
      //   fixedNodeConstraint: fixedNodes.map((n) => ({
      //     nodeId: n.id,
      //     position: n.position,
      //   })),
      // });

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
        }
      }
    },
    [centerNodeInView, setEdges, setLayoutNodes, setNodes, setSelectedNode]
  );

  // On first load show node 1's neighbourhood; on refetch just update fullDataRef
  useEffect(() => {
    if (!data) return;
    const isFirstLoad = fullDataRef.current === null;
    fullDataRef.current = data;
    if (isFirstLoad) prepareGraphData(getSubgraph(data, 1));
  }, [data, prepareGraphData]);

  const onNodeClick = useCallback(
    (_, node) => {
      setCenterNodeId(Number(node.id));
      setSelectedNode(node);
      centerNodeInView(node);
      emitSelectNode?.(Number(node.id));
      if (fullDataRef.current) {
        prepareGraphData(
          getSubgraph(fullDataRef.current, node.id),
          Number(node.id)
        );
      }
    },
    [
      setCenterNodeId,
      setSelectedNode,
      centerNodeInView,
      emitSelectNode,
      prepareGraphData,
    ]
  );

  /** Fit view on container resize */
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const ro = new ResizeObserver(() =>
      fitView({ padding: 0.1, duration: 150 })
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
        onNodeClick={onNodeClick}
        selectNodesOnDrag={false}
        fitView
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
      />
    </div>
  );
}
