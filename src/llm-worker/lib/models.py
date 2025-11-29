from typing import Any, Dict, List, Optional, Set, Union

from dataclasses import dataclass
from fastmcp import Client  # The new high-level client
from loguru import logger

from lib.schemagenerators import ParameterSchema, ToolSchema


@dataclass
class MCPToolReference:
    """
    Reference to an MCP tool from any server.
    Provides a uniform interface regardless of tool source.
    """

    name: str
    description: str
    input_schema: Dict[str, Any]
    _client: Any  # FastMCP Client

    async def __call__(self, **kwargs) -> Any:
        """
        Call the MCP tool with the given arguments.

        Args:
            **kwargs: Tool arguments matching the input_schema

        Returns:
            Tool execution result
        """
        logger.info(f"Calling MCP tool '{self.name}' with args: {kwargs}")
        async with self._client as client:
            result = await client.call_tool(self.name, kwargs)
            logger.debug(f"Found result: {result}")
            if hasattr(result, "content") and len(result.content) > 0:
                logger.debug(f"Returning result.content: {result.content}")
                return result.content[0].text
            logger.warning("No content, returning raw result")
            return result

    def __hash__(self) -> int:
        """Hash based on tool name for set operations."""
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        """Tools are equal if they have the same name."""
        # TODO: maybe create _client.name/tool.name for better uniqueness? Or add schema?
        if not isinstance(other, MCPToolReference):
            return NotImplemented
        return self.name == other.name

    # def __eq__(self, other: object) -> bool:
    #     """Tools are equal if they have the same function and schema"""
    #     if not isinstance(other, Tool):
    #         return NotImplemented
    #     same_func = self.func == other.func
    #     same_schema = self.has_compatible_schema(other)
    #     return same_func and same_schema

    # def has_compatible_schema(self, other: "Tool") -> bool:
    #     """Check if schemas are compatible for LLM use"""
    #     return (
    #         self.schema.parameters == other.schema.parameters
    #         and self.schema.required == other.schema.required
    #     )

    # def __hash__(self) -> int:
    #     """Hash based on function and schema since those determine equality"""
    #     params_tuple = tuple(
    #         sorted((p.name, str(p.param_type)) for p in self.schema.parameters)
    #     )
    #     required_tuple = tuple(sorted(self.schema.required))
    #     return hash((self.func, params_tuple, required_tuple))

    def __str__(self) -> str:
        """String representation is the tool name."""
        return self.name

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"MCPToolReference(name='{self.name}')"

    def get_schema(self) -> ToolSchema:
        """Convert MCP schema to ToolSchema format"""
        properties = self.input_schema.get("properties", {})
        required = self.input_schema.get("required", [])

        parameters = []
        for prop_name, prop_schema in properties.items():
            param = ParameterSchema(
                name=prop_name,
                param_type=prop_schema.get("type", "string"),
                description=prop_schema.get("description"),
                enum=prop_schema.get("enum"),
                nullable=prop_schema.get("nullable"),
            )
            parameters.append(param)

        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=parameters,
            required=required,
        )


class ToolRegistry:
    """Global registry that maintains single instances of tools"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            logger.debug("initializing registry")
            self._tools: Dict[str, MCPToolReference] = {}
            self.initialized = True

    def register(self, tool: "MCPToolReference") -> None:
        """Register a single tool"""
        key = str(tool)
        self._tools[key] = tool
        logger.debug(f"Registered tool: {key}")

    def get(self, name: str) -> "MCPToolReference":
        """Get a tool by name"""
        logger.debug(f"Retrieving tool: {name}")
        if name not in self._tools:
            available = list(self.available_tools)
            logger.debug(f"registry contains: {available}")
            raise ValueError(f"Tool {name} not registered")
        return self._tools[name]

    def reset(self) -> None:
        """Clear all tools from the registry"""
        self._tools = {}
        logger.debug("Tool registry has been reset")

    @property
    def available_tools(self) -> Set[str]:
        """Names of all registered tools"""
        return set(self._tools.keys())


class ToolCollection:
    """
    Represents a view into the tool registry, maintaining only the names
    of tools in this collection.
    Functions like a set:
    - union of two collections : collectionA * collectionB
    - difference of two collections : collectionA - collectionB
    - remove a subset by name : collectionA - ['tool1', 'tool2']
    """

    def __init__(self, tool_names: Optional[Set[str]]):
        self.tool_names: Set[str] = tool_names or set()

        # Validate all tools exist in registry
        self._registry = ToolRegistry()
        unknown = self.tool_names - self._registry.available_tools
        if unknown:
            logger.warning(f"unkown tools in collection: {unknown}")
            logger.debug(f"available tools:{self._registry.available_tools}")
            logger.debug(f"tool_names: {self.tool_names}")
            raise ValueError(f"Unknown tools: {unknown}")

    @classmethod
    def from_tools(cls, tools: list["MCPToolReference"]) -> "ToolCollection":
        """Create a collection from a list of tool functions"""
        registry = ToolRegistry()
        for tool in tools:
            registry.register(tool)
        logger.debug(f"Tools in registry: {registry.available_tools}")
        names = {str(tool) for tool in tools}
        logger.debug(f"creating toolcollection with: {names}")

        return cls(names)

    def get_functions(self) -> list["MCPToolReference"]:
        """Returns list of tool functions"""
        return [self._registry.get(name) for name in self.tool_names]

    def get_schemas(self) -> List[ToolSchema]:
        """Returns list of tool schemas"""
        schemas = []
        for name in self.tool_names:
            logger.debug(f"getting schema for tool: {name}")
            schema = self._registry.get(name).get_schema()
            logger.debug(f"got schema: {schema}")
            schemas.append(schema)
        logger.debug(f"returning schemas: {schemas}")
        return schemas

        # return [self._registry.get(name).get_schema() for name in list(self.tool_names)]

    def __getitem__(self, name: str) -> "MCPToolReference":
        return self._registry.get(name)

    async def __call__(self, tool: str, **kwargs) -> Any:
        """Execute a tool from this collection"""
        if tool not in self:
            raise ValueError(f"Tool {tool} not in this collection")
        ref = self._registry.get(tool)
        logger.debug(f"Executing tool {tool} with args: {kwargs}")
        return await ref(**kwargs)

    def __contains__(self, item: str) -> bool:
        """Check if a tool is in this collection"""
        return item in self.tool_names

    def __mul__(self, other: "ToolCollection") -> "ToolCollection":
        """Combines two tool collections"""
        return ToolCollection(self.tool_names | other.tool_names)

    def __sub__(
        self, other: Union["ToolCollection", Set[str], List[str]]
    ) -> "ToolCollection":
        """Remove tools by name"""
        if isinstance(other, ToolCollection):
            exclude = other.tool_names
        elif isinstance(other, (set, list)):
            exclude = set(other)
        else:
            raise TypeError(f"Unsupported type for subtraction: {type(other)}")
        return ToolCollection(self.tool_names - exclude)

    def __str__(self) -> str:
        names = [str(n) for n in self.tool_names]
        return f"ToolCollection({names}))"

    def __repr__(self) -> str:
        names = [str(n) for n in self.tool_names]
        return f"ToolCollection({names})"

    def __len__(self) -> int:
        """Number of tools in the collection"""
        return len(self.tool_names)
