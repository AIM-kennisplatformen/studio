/* Copied from PoC-Robert-React-Flow */
import { useCallback, useEffect } from 'react';
import { ReactFlow, applyEdgeChanges, addEdge, useReactFlow } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './App.css';
import { Button } from './components/ui/button';
import { CustomNode } from './components/CustomNode';
import { useDataToGraphTransformer, useUpdateGraphTransformer } from './hooks/useGraphTransformer';
import { useAtom,useSetAtom } from 'jotai';
import { nodesAtom, selectedNodeAtom , edgesAtom, draggingNodeIdAtom} from './data/atoms';
import { useUpdateNodesPostions } from './hooks/useGraphTransformer';
import { useFlowAnimation } from './hooks/useFlowAnimation';

export default function Graph({ data, width }) {
  const { setViewport, getViewport, updateNodeInternals } = useReactFlow();
  const selectedNode = useSetAtom(selectedNodeAtom);
  const [nodes, setNodes] = useAtom(nodesAtom);
  const [edges, setEdges] = useAtom(edgesAtom);
  const setDraggingNodeId = useSetAtom((draggingNodeIdAtom));
  const updater = useUpdateGraphTransformer(updateNodeInternals);
  const nodeUpdater = useUpdateNodesPostions(getViewport, setViewport);

  // Convert knowledge graph data to React Flow nodes and edges
    useDataToGraphTransformer(data);

  // Function to update edge handles based on node positions
  const updateEdgePositions = useCallback((currentNodes, currentEdges) => {
   return updateEdgePositions(currentNodes, currentEdges);
  }, []);

  // Update node and edge styling based on selection
  useEffect(() => {
    updater();
  }, [updater, selectedNode]);

  // Use the custom animation hook
  const { randomizePositions, applyAvsdfPositions, applyColaPositions, applyFcosePositions, isAnimating } = useFlowAnimation(nodes, edges, setNodes, setEdges, updateEdgePositions);
  
  const onNodesChange = useCallback(
    (changes, setNodes) => {
      return nodeUpdater(changes, setNodes);
    },
    [nodeUpdater],
  );


  const onEdgesChange = useCallback(
    (changes) => setEdges((edgesSnapshot) => applyEdgeChanges(changes, edgesSnapshot)),
    [setEdges],
  );
  const onConnect = useCallback(
    (params) => setEdges((edgesSnapshot) => addEdge(params, edgesSnapshot)),
    [setEdges],
  );

  // Track when dragging starts
  const onNodeDragStart = useCallback((event, node) => {
    setDraggingNodeId(node.id);
  }, [setDraggingNodeId]);

  // Track when dragging stops
  const onNodeDragStop = useCallback(() => {
    setDraggingNodeId(null);
  }, [setDraggingNodeId]);


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
    <div style={{
      width: '100vw',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#f5f5f5',
    }}>
      <div style={{
        padding: '10px',
        background: '#333',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h1 style={{ margin: 0, fontSize: '20px' }}>Music Knowledge Graph</h1>
          {nodes.length > 0 && (
            <span style={{ fontSize: '14px' }}>
              {nodes.length} entities • {edges.length} relationships
            </span>
          )}
        </div>
        {nodes.length > 0 && (
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
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
      <div style={{ flex: 1, position: 'relative' }}>
        <ReactFlow  width={width} height="100%"
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
      <div style={{
        padding: '10px',
        background: '#333',
        color: 'white',
        fontSize: '12px',
        display: 'flex',
        gap: '20px'
      }}>
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