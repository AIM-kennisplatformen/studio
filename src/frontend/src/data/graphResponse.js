const BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL;  


export async function fetchGraphAnswer() {
    const url = `${BASE_URL}/graph`;

    const FALLBACK_GRAPH = { nodes: [], edges: [] }; 
    try {
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        // Backend returned error status → fallback
        return FALLBACK_GRAPH;
      }

      const data = await response.json();

      if (data && (data.nodes || data.edges)) {
        return { nodes: data.nodes ?? [], edges: data.edges ?? [], selected_subnode: data.selected_subnode ?? null };
      }
      // Backend returned empty or malformed data: fallbackl,
      // should not happen with current backend implementation (unreachable)
      return FALLBACK_GRAPH;

    } catch (err) {
      console.warn("Failed to fetch graph:", err);
      return FALLBACK_GRAPH; // fallback to mock data on any error
    }
  }