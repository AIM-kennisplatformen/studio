from studio.mcp.scepa.paper_search import mcp

if __name__ == "__main__":
    # asyncio.run(main())
    mcp.settings.host = "0.0.0.0"
    mcp.run(transport="sse")
