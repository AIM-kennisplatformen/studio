from typing import Any, List, Dict

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

    # ------------------------------------------------------
    # TOOL COLLECTION
    # ------------------------------------------------------
    def get_tools(self) -> ToolCollection:
        registry = ToolRegistry()
        all_tools = ToolCollection(registry.available_tools)

        if self.allowed_tools is None:
            logger.debug(f"All tools allowed: {all_tools.tool_names}")
            return all_tools

        unknown = set(self.allowed_tools) - registry.available_tools
        if unknown:
            raise ValueError(f"Unknown tools requested: {unknown}")

        excluded = registry.available_tools - set(self.allowed_tools)
        logger.debug(f"Excluded tools: {excluded}")

        allowed = all_tools - excluded
        logger.debug(f"Allowed tools: {allowed}")

        return allowed

    # ------------------------------------------------------
    # CLIENT INITIALIZATION
    # ------------------------------------------------------
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

    # ------------------------------------------------------
    # NON-STREAMING CALLS
    # ------------------------------------------------------
    def _anthropic_call(self, messages, **kwargs) -> Any:
        assert isinstance(self.client, Anthropic)
        return self.client.messages.create(
            model=self.config.model_type.value,
            messages=messages,
            max_tokens=self.config.max_tokens,
            **kwargs,
        )

    def _ollama_call(self, messages, **kwargs) -> Any:
        """Standard non-streaming call (unchanged)."""
        assert isinstance(self.client, OllamaClient)
        logger.debug(f"Calling Ollama: {self.config.model_type}")
        return self.client.chat(
            model=self.config.model_type,
            messages=messages,
            stream=False,
            **kwargs,
        )

    async def __call__(self, messages, **kwargs):
        if self.config.client_type == ClientType.ANTHROPIC:
            adapter = AnthropicAdapter
        else:
            adapter = LlamaAdapter

        tools = self.get_tools()
        schemas = tools.get_schemas()
        formatted_tools = [adapter.format_schema(schema) for schema in schemas]

        return await self._tool_loop(
            call_func=(self._anthropic_call if self.config.client_type == ClientType.ANTHROPIC else self._ollama_call),
            messages=messages,
            adapter=adapter,
            tools=formatted_tools,
            **kwargs,
        )

    async def _tool_loop(self, call_func, messages, adapter, **kwargs):
        try:
            response = call_func(messages=messages, **kwargs)
            messages = adapter.append_message(messages, response)

            tool_calls = adapter.extract_tool_calls(response)
            toolcollection = self.get_tools()

            if tool_calls:
                for tool in tool_calls:
                    toolcall = adapter.parse_tool_call(tool)
                    output = await toolcollection(toolcall["name"], **toolcall["args"])
                    tool_response = adapter.format_tool_response(toolcall, output)
                    messages.append(tool_response)

                response = call_func(messages=messages, **kwargs)

            return response

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

