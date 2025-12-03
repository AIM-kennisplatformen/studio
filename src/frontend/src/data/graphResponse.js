import responsesFromId from "./graphMockData.js";

function getMockData(nodeId){
  return responsesFromId[nodeId] || [];
}
   


export async function fetchGraphAnswer(nodeId) {
  const url = `http://kg.localhost:8090/nodes/${nodeId}/context`;

  try {
    const response = await fetch(url, {
      method: "GET",
      credentials: "include",   // <-- REQUIRED for cookie-based Auth!
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nodeId }),
    });
    

    if (!response.ok) {
      // Backend returned an error status
      console.error("Failed to fetch graph nodes:", response.statusText);
    }

    const data = await response.json();

    if (!data.nodes && !data.edges) {
        // If the response doesn't have nodes or edges, return mock data
        return getMockData(nodeId);
    }

    console.log("Fetched graph nodes:", data);
    return data;

  } catch (err) {
    // Network error, server not running, etc.
    console.error("Failed to fetch graph nodes:", err);
  }
}



