"""
MCP Connection Manager (Refactored with fastmcp)
Manages connections to multiple MCP servers and tool discovery.
"""

from typing import Dict, List

from fastmcp import Client  # The new high-level client
from loguru import logger

from lib.models import MCPToolReference, ToolCollection

class MCPConnectionManager:
    """
    Manages connections to MCP servers using the fastmcp library.
    Automatically handles transport detection (Stdio vs HTTP).
    """

    def __init__(self):
        # Stores active fastmcp.Client instances
        self._clients: Dict[str, Client] = {}

    @property
    def connected_servers(self) -> List[str]:
        return list(self._clients.keys())

    async def connect_server(
        self,
        name: str,
        target: str,
    ) -> None:
        """
        Connect to an MCP server. The transport is inferred from the target.

        Args:
            name: Unique name for this server connection
            target: The connection string.
                    - URL (e.g., "http://localhost:8000") -> HTTP
                    - Path (e.g., "./server.py", "mcp-server-git") -> Stdio
        """
        if name in self._clients:
            logger.warning(f"Server '{name}' already connected")
            return

        logger.debug(f"Connecting to MCP server '{name}' at target: {target}")

        try:
            client = Client(target)

            async with client:
                await client.ping()
                self._clients[name] = client
                logger.info(f"Successfully connected to MCP server '{name}'")

        except Exception as e:
            logger.error(f"Failed to connect to '{name}': {e}")
            raise e

    async def list_tools(self, server_name: str) -> list[str]:
        """
        List the names of tools available from a connected server.
        """
        if server_name not in self._clients:
            raise ValueError(f"Server '{server_name}' is not connected")

        client = self._clients[server_name]
        async with client:
            try:
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
                return tool_names
            except Exception as e:
                logger.error(f"Error listing tools for '{server_name}': {e}")
                raise e

    async def get_tools(self, server_name: str) -> ToolCollection:
        """
        return all tools available from a connected server as a callable toolcollection
        """
        if server_name not in self._clients:
            raise ValueError(f"Server '{server_name}' is not connected")

        client = self._clients[server_name]

        try:
            logger.debug(f"Discovering tools from server '{server_name}'")
            async with client:
                tools_list = await client.list_tools()

                tool_refs = []
                for tool in tools_list:
                    tool_ref = MCPToolReference(
                        name=tool.name,
                        description=tool.description or "",
                        input_schema=tool.inputSchema,
                        _client=client,  # Passing the high-level client
                    )
                    tool_refs.append(tool_ref)

            logger.info(f"Discovered {len(tool_refs)} tools from '{server_name}'")
            toolcollection = ToolCollection.from_tools(tool_refs)
            return toolcollection

        except Exception as e:
            logger.error(f"Error discovering tools for '{server_name}': {e}")
            raise e

    async def disconnect_server(self, name: str) -> None:
        """
        Disconnect from a specific server.
        """
        if name not in self._clients:
            logger.warning(f"Server '{name}' is not connected")
            return

        client = self._clients[name]
        try:
            # Manually exit the context to clean up resources
            await client.__aexit__(None, None, None)
            del self._clients[name]
            logger.info(f"Disconnected from server '{name}'")
        except Exception as e:
            logger.error(f"Error during disconnect of '{name}': {e}")

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        server_names = list(self._clients.keys())
        for name in server_names:
            await self.disconnect_server(name)
        logger.info("Disconnected from all servers")

    def is_connected(self, name: str) -> bool:
        return name in self._clients
