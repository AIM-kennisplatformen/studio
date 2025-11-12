/* Copied from PoC-Robert-React-Flow */
import knowledgeGraph from '../data/knowledgeGraph.json';

// Function to transform knowledge graph data into nodes and edges
export function transformKnowledgeGraph() {
const nuggetMap = new Map(knowledgeGraph.nuggets.map(n => [n.id, n]));
    
    // Convert all nuggets to nodes format
    const allNodes = knowledgeGraph.nuggets.map(nugget => {
      let displayYear = 'N/A';
      if (nugget.release_year) displayYear = nugget.release_year;
      else if (nugget.formed_year) displayYear = nugget.formed_year;
      else if (nugget.birth_year) displayYear = nugget.birth_year;
      
      return {
        id: nugget.id,
        title: nugget.title,
        released: displayYear,
        type: nugget.type || 'nugget',
        description: nugget.description || ''
      };
    });
    
    // Convert all relationships to edges format
    const allEdges = knowledgeGraph.relationships.map(rel => {
      const sourceEntity = nuggetMap.get(rel.source_id);
      const targetEntity = nuggetMap.get(rel.target_id);
      
      return {
        id: rel.id,
        source: rel.source_id,
        target: rel.target_id,
        label_forward: rel.label_forward,
        label_backward: rel.label_backward,
        description: rel.description || '',
        // For compatibility with existing visualization
        sourceTitle: sourceEntity?.title || '',
        targetTitle: targetEntity?.title || ''
      };
    });
    
    // Structure data for the App component
    // Since the App expects "person", "movies", "coworkers" format,
    // we'll adapt it to show all data in a flattened structure
    const data = {
      allNodes: allNodes,
      allEdges: allEdges,
      person: null, // No central person
      movies: [], // Will be populated by App from allNodes/allEdges
      coworkers: [] // Will be populated by App from allNodes/allEdges
    };
    return data;
}