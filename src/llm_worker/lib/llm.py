from typing import Any

from anthropic import Anthropic
from loguru import logger
from ollama import Client as OllamaClient

from lib.schemagenerators import AnthropicAdapter, LlamaAdapter
from lib.settings import ClientType, ModelConfig
from lib.models import ToolCollection, ToolRegistry



class LLMClient:
    def __init__(self, config: ModelConfig):
        self.config: ModelConfig = config
        self.client = self._initialize_client()
        self.allowed_tools = config.allowed_tools

    def __repr__(self) -> str:
        return f"LLMClient(model={self.config.model_type.value})"

    def get_tools(self) -> ToolCollection:
        registry = ToolRegistry()
        all_tools = ToolCollection(registry.available_tools)

        allowed: ToolCollection

        if self.allowed_tools is None:
            allowed = all_tools
            logger.debug(f"All tools allowed: {allowed.tool_names}")
        else:
            unknown = set(self.allowed_tools) - registry.available_tools
            if unknown:
                raise ValueError(f"Unknown tools requested: {unknown}")

            excluded = registry.available_tools - set(self.allowed_tools)
            logger.debug(f"Excluded tools: {excluded}")

            allowed = all_tools - excluded
            logger.debug(f"Allowed tools: {allowed}")

        return allowed


    def _initialize_client(self):
        if self.config.client_type == ClientType.ANTHROPIC:
            if not self.config.max_tokens:
                raise ValueError("max_tokens required for Anthropic")
            return Anthropic()
        elif self.config.client_type == ClientType.OLLAMA:
            if not self.config.host:
                raise ValueError("host required for Ollama")
            logger.debug(f"Connecting to Ollama at {self.config.host}")
            return OllamaClient(host=str(self.config.host))
        else:
            raise ValueError(f"Unsupported client type: {self.config.client_type}")

    def _anthropic_call(self, messages, **kwargs) -> Any:
        assert isinstance(self.client, Anthropic), (
            f"Expected Anthropic, got {type(self.client)}"
        )
        return self.client.messages.create(
            model=self.config.model_type.value,
            messages=messages,
            max_tokens=self.config.max_tokens,
            **kwargs,
        )

    def _ollama_call(self, messages, **kwargs) -> Any:
        assert isinstance(self.client, OllamaClient), (
            f"Expected OllamaClient, got {self.client}"
        )
        logger.debug(f"Calling Ollama :{self.config.model_type}")
        return self.client.chat(
            model=self.config.model_type, messages=messages, **kwargs
        )

    async def __call__(self, messages, **kwargs):
        if self.config.client_type == ClientType.ANTHROPIC:
            logger.debug("Using Anthropic")
            adapter = AnthropicAdapter
            tools = self.get_tools()
            schemas = tools.get_schemas()
            logger.success("Retrieved tool schemas")
            tools = [adapter.format_schema(schema) for schema in schemas]
            logger.debug(f"Using Anthropic adapter with tools: {tools}")
            return await self._tool_loop(
                call_func=self._anthropic_call,
                messages=messages,
                adapter=adapter,
                tools=tools,
                **kwargs,
            )
        elif self.config.client_type == ClientType.OLLAMA:
            logger.debug("Using Ollama")
            adapter = LlamaAdapter
            tools = self.get_tools()
            schemas = tools.get_schemas()
            logger.success("Retrieved tool schemas")
            tools = [adapter.format_schema(schema) for schema in schemas]
            logger.debug(f"Using Ollama adapter with tools: {tools}")
            return await self._tool_loop(
                self._ollama_call,
                messages=messages,
                adapter=adapter,
                tools=tools,
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported client type: {self.config.client_type}")

    async def _tool_loop(self, call_func, messages, adapter, **kwargs):
        try:
            response = call_func(messages=messages, **kwargs)
            messages = adapter.append_message(messages, response)

            # Use the adapter to extract tool calls
            tool_calls = adapter.extract_tool_calls(response)
            toolcollection = self.get_tools()

            if tool_calls:
                for tool in tool_calls:
                    toolcall = adapter.parse_tool_call(tool)
                    schema = toolcollection[toolcall["name"]].get_schema()
                    logger.debug(f"From tool {toolcall['name']} got schema: {schema}")

                    # for p in schema.parameters:
                    #     logger.debug(
                    #         f"Checking if {p.name} is nullable {p.nullable} for arg {toolcall['args'][p.name]}"
                    #     )
                    #     if (
                    #         p.name in toolcall["args"]
                    #         and p.nullable
                    #         and toolcall["args"][p.name] in [None, "", "null", "None"]
                    #     ):
                    #         toolcall["args"][p.name] = None

                    logger.info(
                        f"LLM decides to use tool: {toolcall['name']} with {toolcall['args']}"
                    )
                    try:
                        if toolcall["name"] not in toolcollection:
                            logger.warning(
                                f"Tool {toolcall['name']} not allowed collection"
                            )
                            continue

                        output = await toolcollection(
                            toolcall["name"], **toolcall["args"]
                        )

                        # Format tool response using the adapter
                        tool_response = adapter.format_tool_response(toolcall, output)
                        messages.append(tool_response)

                    except (AttributeError, ValueError) as e:
                        logger.error(f"Tool execution failed: {e}")
                        tool_response = adapter.format_tool_response(toolcall, e)
                        messages.append(tool_response)
                        continue

                logger.debug(f"Messages after tool calls: {messages}")
                response = call_func(messages=messages, **kwargs)

            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
