import { responsesFromId } from './graphMockData.js'

/**
 * Return mock data for a nodeId
 */
function getMockData(nodeId) {
  const resp = responsesFromId[nodeId] ?? responsesFromId[String(nodeId)]
  return {
    nodes: resp?.nodes ?? [],
    edges: resp?.edges ?? [],
  }
}

/**
 * Fetch graph nodes & edges for a given nodeId.
 * Uses backend if reachable, otherwise returns mock data.
 */
export async function fetchGraphAnswer(nodeId = '1') {
  /*
  const url = `http://kg.localhost:8090/nodes/${nodeId}/context`;

  try {
    const response = await fetch(url, {
      method: "GET",
      credentials: "include", // required for cookie auth
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      // Backend returned error status → fallback
      return getMockData(nodeId) ;
    }

    const data = await response.json();

    // If backend returns nodes/edges, normalize them
    if (data && (data.nodes || data.edges)) {
      return {
        nodes: data.nodes ?? [],
        edges: data.edges ?? [],
      };
    }

    // Backend returned empty data → fallback
    return getMockData(nodeId);

  } catch (err) {
    // Network error, backend not running, CORS, etc.
    console.warn("Failed to fetch graph, using mock data:", err);
    console.log("Fetch graph for nodeId:", nodeId);
    console.log("Returning mock data:", getMockData(nodeId));
    return getMockData(nodeId);
    */
  return getMockData(nodeId)
}
