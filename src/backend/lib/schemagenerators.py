import inspect
import json
from abc import ABC, abstractmethod
from enum import Enum
from inspect import Parameter, signature
from pathlib import Path
from string import Template
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from loguru import logger
from pydantic import BaseModel

from lib.settings import ClientType

if TYPE_CHECKING:
    from lib.llm import LLMClient


SCHEMA_PROMPT_TEMPLATE = Template("""Given this Python function information:
source: ${source}
Basic schema: ${basic_schema}
docs: ${docs}

Please extend this with clear, detailed descriptions of what this function and each parameter does.
respond with the following JSON schema:
{
    "description": "A clear, detailed description of what this function does",
    "parameters": {
        "param1": {
            "description": "A clear, detailed description of what this parameter does",
        },
    },
}
reply with the JSON schema only, and nothing else
""")


class ParameterSchema(BaseModel):
    name: str
    param_type: str
    description: Optional[str] = None
    enum: Optional[list[str]] = None
    nullable: Optional[bool] = None


class ToolSchema(BaseModel):
    """Represents the schema for a tool, following Anthropic's format"""

    name: str
    description: str
    parameters: list[ParameterSchema]
    required: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def __repr__(self) -> str:
        dict_schema = self.to_dict()
        return f"ToolSchema({dict_schema})"

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string for easy viewing/editing"""
        return self.model_dump_json(indent=indent)

    def to_file(self, file_path: Path, indent: int = 2) -> None:
        """Write schema to a JSON file

        Args:
            file_path: Path where the JSON file will be saved
            indent: Number of spaces for indentation in the JSON file
        """
        with file_path.open("w") as f:
            f.write(self.to_json(indent=indent))

    @classmethod
    def from_json(cls, json_str: str) -> "ToolSchema":
        """Create schema from JSON string"""
        data = json.loads(json_str)
        return cls(
            name=data["name"],
            description=data["description"],
            parameters=data["parameters"],
            required=data["required"],
        )

    @classmethod
    def from_file(cls, file_path: Path) -> "ToolSchema":
        """Create schema from a JSON file
        Args:
            file_path: Path to the JSON file containing the schema

        Returns:
            A new ToolSchema instance with data from the file
        """
        with file_path.open("r") as f:
            json_str = f.read()
        return cls.from_json(json_str)


class LLMAdapter(ABC):
    """Abstract base class for LLM client adapters."""

    @classmethod
    @abstractmethod
    def format_schema(cls, toolschema: ToolSchema) -> Dict[str, Any]:
        """Format tool schema for the specific LLM."""
        pass

    @classmethod
    @abstractmethod
    def format_parameter(cls, parameter: ParameterSchema) -> Dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def get_content(cls, response) -> str:
        """Get content from LLM response."""
        pass

    @classmethod
    @abstractmethod
    def append_message(cls, messages: List, response) -> List:
        pass

    @classmethod
    @abstractmethod
    def extract_tool_calls(cls, response) -> List:
        """Extract tool calls from LLM response."""
        pass

    @classmethod
    @abstractmethod
    def parse_tool_call(cls, tool) -> dict[str, Any]:
        """Parse tool call to extract name and arguments."""
        pass

    @classmethod
    @abstractmethod
    def format_tool_response(cls, toolcall: dict, output) -> Dict[str, Any]:
        """Format tool response for the LLM."""
        pass


class AnthropicAdapter(LLMAdapter):
    @classmethod
    def format_schema(cls, toolschema: ToolSchema) -> Dict[str, Any]:
        return {
            "name": toolschema.name,
            "description": toolschema.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    p.name: cls.format_parameter(p) for p in toolschema.parameters
                },
                "required": toolschema.required,
            },
        }

    @classmethod
    def format_parameter(cls, parameter: ParameterSchema) -> Dict[str, Any]:
        param_dict: Dict[str, Any] = {"type": parameter.param_type}
        if parameter.description:
            param_dict["description"] = parameter.description
        if parameter.enum:
            param_dict["enum"] = parameter.enum
        if parameter.nullable:
            param_dict["nullable"] = parameter.nullable
        return param_dict

    @classmethod
    def append_message(cls, messages: List, response) -> List:
        messages.append({"role": "assistant", "content": response.content})
        return messages

    @classmethod
    def get_content(cls, response) -> str:
        return response.content

    @classmethod
    def extract_tool_calls(cls, response) -> List:
        if hasattr(response, "content"):
            return [
                block
                for block in response.content
                if getattr(block, "type", None) == "tool_use"
            ]
        return []

    @classmethod
    def parse_tool_call(cls, tool) -> dict[str, Any]:
        return {
            "id": tool.id,
            "name": tool.name,
            "args": tool.input,
        }

    @classmethod
    def format_tool_response(cls, toolcall: dict, output) -> Dict[str, Any]:
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": toolcall["id"],
                    "content": str(output),
                }
            ],
        }


class LlamaAdapter(LLMAdapter):
    @classmethod
    def format_schema(cls, toolschema: ToolSchema) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": toolschema.name,
                "description": toolschema.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        p.name: cls.format_parameter(p) for p in toolschema.parameters
                    },
                    "required": toolschema.required,
                },
            },
        }

    @classmethod
    def format_parameter(cls, parameter: ParameterSchema) -> Dict[str, Any]:
        param_dict: Dict[str, Any] = {"type": parameter.param_type}
        if parameter.description:
            param_dict["description"] = parameter.description
        if parameter.enum:
            param_dict["enum"] = parameter.enum
        if parameter.nullable:
            param_dict["nullable"] = parameter.nullable
        return param_dict

    @classmethod
    def append_message(cls, messages: List, response) -> List:
        messages.append(response.message)
        return messages

    @classmethod
    def get_content(cls, response) -> str:
        return response.message.content

    @classmethod
    def extract_tool_calls(cls, response) -> List:
        if hasattr(response.message, "tool_calls") and response.message.tool_calls:
            return response.message.tool_calls
        return []

    @classmethod
    def parse_tool_call(cls, tool) -> dict[str, Any]:
        return {
            "name": tool.function.name,
            "args": tool.function.arguments,
        }

    @classmethod
    def format_tool_response(cls, toolcall: dict, output) -> Dict[str, Any]:
        return {
            "role": "tool",
            "content": str(output),
            "name": toolcall["name"],
        }


class SchemaGenerator(ABC):
    """Abstract base class for schema generators"""

    @abstractmethod
    def generate_schema(self, func: Callable) -> ToolSchema:
        pass


class BasicSchemaGenerator(SchemaGenerator):
    """Basic schema generator using inspect module"""

    _TYPE_MAP = {
        int: {"param_type": "integer"},
        float: {"param_type": "number"},
        str: {"param_type": "string"},
        bool: {"param_type": "boolean"},
        list: {"param_type": "array"},
        dict: {"param_type": "object"},
    }

    def generate_schema(self, func: Callable) -> ToolSchema:
        sig = signature(func)
        type_hints = get_type_hints(func)
        parameters = []
        required = []

        for name, param in sig.parameters.items():
            param_type = type_hints.get(name, Any)

            # Skip self parameter for methods
            if name == "self":
                continue
            # Inside generate_schema
            param_schema = self._process_type(name, param_type)

            # Handle default values
            if param.default is Parameter.empty:
                required.append(name)

            parameters.append(param_schema)

        # Get description from docstring
        description = self._get_function_doc(func)
        return ToolSchema(
            name=func.__name__,
            description=description,
            parameters=parameters,
            required=required,
        )

    def _get_function_doc(self, func):
        """Extract function documentation"""
        return inspect.getdoc(func) or f"Function {func.__name__}"

    def _process_type(self, name, param_type) -> ParameterSchema:
        """Process a type hint to generate the appropriate schema"""
        # Handle Optional types (Union[X, None])
        origin = get_origin(param_type)
        args = get_args(param_type)

        # Handle Optional[X] -> Union[X, None]
        if origin is Union:
            if type(None) in args:
                # Get the non-None type
                non_none_type = next(arg for arg in args if arg is not type(None))
                param_schema = self._process_type(name, non_none_type)
                param_schema.nullable = True
                return param_schema

        # Handle Enum types
        if isinstance(param_type, type) and issubclass(param_type, Enum):
            return ParameterSchema(
                **{
                    "name": name,
                    "param_type": "string",
                    "enum": [item.value for item in param_type],
                }
            )

        # Handle basic types
        if param_type in self._TYPE_MAP:
            # dict is necessary to avoid overwriting the typemap
            basic_type = dict(self._TYPE_MAP[param_type])
            return ParameterSchema(**{"name": name, **basic_type})

        # Default to string for unknown types
        return ParameterSchema(**{"name": name, "param_type": "string"})


class LLMSchemaGenerator(SchemaGenerator):
    """Schema generator that uses LLM to generate high-quality descriptions"""

    def __init__(self, llm_client: "LLMClient"):
        self.llm = llm_client
        self.basic_generator = BasicSchemaGenerator()

    def generate_schema(self, func: Callable) -> ToolSchema:
        # First get basic schema for structure
        basic_schema = self.basic_generator.generate_schema(func)
        try:
            info = {
                "source": inspect.getsource(func),
                "basic_schema": basic_schema,
                "docs": self.basic_generator._get_function_doc(func),
            }
            content = SCHEMA_PROMPT_TEMPLATE.substitute(info)
            messages = [{"role": "user", "content": content}]
            try:
                response = self.llm(messages)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return basic_schema

            try:
                adapter = None
                if self.llm.config.client_type == ClientType.ANTHROPIC:
                    adapter = AnthropicAdapter
                elif self.llm.config.client_type == ClientType.OLLAMA:
                    adapter = LlamaAdapter
                if adapter is None:
                    raise ValueError(
                        f"Unsupported client type: {self.llm.config.client_type}"
                    )
                content = adapter.get_content(response)
                enhanced = json.loads(content)
            except json.JSONDecodeError:
                import re

                enhanced = None
                json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
                if json_match:
                    enhanced = json.loads(json_match.group(1))
                if not enhanced:
                    logger.warning("LLM enahncement failed, using basic schema")
                    logger.debug(f"got content: {content}")
                    return basic_schema
            try:
                basic_schema.description = enhanced["description"]
                for param in basic_schema.parameters:
                    if param.name in enhanced["parameters"]:
                        param.description = enhanced["parameters"][param.name][
                            "description"
                        ]
                return basic_schema
            except KeyError as e:
                logger.error(f"LLM response missing key: {e}")
                return basic_schema
        except Exception as e:
            logger.error(f"Error generating schema: {e}")
            return basic_schema
