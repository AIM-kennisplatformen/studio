"""
MCP Tool Loader
Factory for loading tools from MCP servers using the fastmcp connection manager.
"""



from lib.models import ToolCollection

from lib.mcp_client import MCPConnectionManager




class MCPToolLoader:
    """
    Factory for loading tools from MCP servers.
    """

    def __init__(self, connection_manager=None):
        self.connection_manager = connection_manager or MCPConnectionManager()

    async def load_server(
        self,
        name: str,
        target: str,
    ) -> ToolCollection:
        """
        Connect to an MCP server and load its tools.
        FastMCP automatically infers the transport based on the 'target' argument:

        1. FastMCP instance → In-memory transport (perfect for testing)
        2. File path ending in .py → Python Stdio transport
        3. File path ending in .js → Node.js Stdio transport
        4. URL starting with http:// or https:// → HTTP transport
        5. MCPConfig dictionary → Multi-server client

        Args:
            name: Unique name for this server connection
            target: Connection string (e.g., 'http://localhost:8000', 'my_script.py')

        Returns:
            ToolCollection containing all tools from the server
        """

        # Connect to server (ConnectionManager handles transport detection)
        await self.connection_manager.connect_server(
            name=name,
            target=target,
        )

        # Discover tools
        toolcollection = await self.connection_manager.get_tools(name)
        return toolcollection

    async def cleanup(self) -> None:
        """Disconnect from all servers"""
        await self.connection_manager.disconnect_all()
