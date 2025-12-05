from typing import Any, List, Dict

from anthropic import Anthropic
from loguru import logger

from lib.schemagenerators import AnthropicAdapter, LlamaAdapter
from lib.settings import ClientType, ModelConfig
from lib.models import ToolCollection, ToolRegistry
from dotenv import load_dotenv

load_dotenv()
import os
print("Langfuse Host:", os.getenv("LANGFUSE_HOST"))
print("Langfuse Public:", os.getenv("LANGFUSE_PUBLIC_KEY"))
print("Langfuse Secret:", os.getenv("LANGFUSE_SECRET_KEY"))

from langfuse.openai import OpenAI

class LLMClient:
    def __init__(self, config: ModelConfig):
        self.config: ModelConfig = config
        self.client = self._initialize_client()
        self.allowed_tools = config.allowed_tools

    def __repr__(self) -> str:
        return f"LLMClient(model={self.config.model_type.value})"
    def _normalize_response(self, response):
        # Anthropics return .message
        if hasattr(response, "message"):
            return response.message
        
        # OpenAI/Ollama return choices[0].message
        if hasattr(response, "choices"):
            return response.choices[0].message

        raise ValueError("Unknown response format")

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
            return OpenAI(base_url=str(self.config.host), api_key=str(self.config.api_key))

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
        """Standard non-streaming call with tool sanitization."""
        assert isinstance(self.client, OpenAI)
        logger.debug(f"Calling Ollama: {self.config.model_type}")

        # --- FIX: clean tools list ---
        tools = kwargs.get("tools")
        if tools is not None:
            # Remove None or invalid entries
            cleaned_tools = [t for t in tools if isinstance(t, dict)]
            kwargs["tools"] = cleaned_tools if cleaned_tools else None

        # Optional: log what tools are being used
        logger.debug(f"Tools passed to model: {kwargs.get('tools')}")

        return self.client.chat.completions.create(
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
            raw_response = call_func(messages=messages, **kwargs)
            response = self._normalize_response(raw_response)

            messages = adapter.append_message(messages, response)

            tool_calls = adapter.extract_tool_calls(response)
            toolcollection = self.get_tools()

            if tool_calls:
                for tool in tool_calls:
                    toolcall = adapter.parse_tool_call(tool)
                    output = await toolcollection(toolcall["name"], **toolcall["args"])
                    tool_response = adapter.format_tool_response(toolcall, output)
                    messages.append(tool_response)

                raw_response = call_func(messages=messages, **kwargs)
                response = self._normalize_response(raw_response)

            return raw_response

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

