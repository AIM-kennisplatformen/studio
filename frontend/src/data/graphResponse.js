import { BACKEND_BASE_URL } from "./api.js";

const FALLBACK_GRAPH = { nodes: [], edges: [] };

export async function fetchGraphAnswer(focusId = null, hops = 1) {
  const params = new URLSearchParams();
  if (focusId != null) {
    params.set("focus", String(focusId));
    params.set("hops", String(hops));
  }
  const query = params.toString();
  const url = `${BACKEND_BASE_URL}/graph${query ? `?${query}` : ""}`;

  try {
    const response = await fetch(url, {
      method: "GET",
      credentials: "include",
    });

    if (!response.ok) {
      // Backend returned error status → fallback
      return FALLBACK_GRAPH;
    }

    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      throw new Error(
        `Expected JSON from ${url}, got ${contentType || "unknown content type"}`
      );
    }

    const data = await response.json();

    if (data && (data.nodes || data.edges)) {
      return {
        nodes: data.nodes ?? [],
        edges: data.edges ?? [],
        selected_subnode: data.selected_subnode ?? null,
        focus_node_id: data.focus_node_id ?? null,
        error: data.error ?? null,
      };
    }
    // Backend returned empty or malformed data: fallback,
    // should not happen with current backend implementation (unreachable)
    return FALLBACK_GRAPH;
  } catch (err) {
    console.warn("Failed to fetch graph:", err);
    return FALLBACK_GRAPH; // fallback to mock data on any error
  }
}

// POC(fcose): options for the temporary focus picker. Replace with a
// query-driven selection once the MCP server returns the subgraph.
export async function fetchGraphOptions() {
  const url = `${BACKEND_BASE_URL}/graph/options`;

  try {
    const response = await fetch(url, {
      method: "GET",
      credentials: "include",
    });
    if (!response.ok) return [];

    const data = await response.json();
    return Array.isArray(data?.options) ? data.options : [];
  } catch (err) {
    console.warn("Failed to fetch graph options:", err);
    return [];
  }
}
