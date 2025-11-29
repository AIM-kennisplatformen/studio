from mcp_servers.mcp.scepa.paper_search import mcp

if __name__ == "__main__":
    mcp.settings.host="0.0.0.0"
    mcp.run(transport="sse")
