from typing import Any, Optional, Union
from unittest.mock import patch

import pytest
from loguru import logger

from llm_tooluse.schemagenerators import ToolSchema


def test_basic_schema_creation(basic_schema):
    """Test basic creation of ToolSchema"""
    assert basic_schema.name == "test_function"
    assert basic_schema.description == "A test function"
    assert basic_schema.parameters[0].name == "param1"
    assert basic_schema.parameters[0].param_type == "string"
    assert basic_schema.required == ["param1"]


def test_schema_to_dict(basic_schema):
    """Test conversion of schema to dictionary format"""
    expected_dict = {
        "name": "test_function",
        "description": "A test function",
        "parameters": [
            {
                "name": "param1",
                "param_type": "string",
                "description": None,
                "enum": None,
                "nullable": None,
            }
        ],
        "required": ["param1"],
    }

    assert basic_schema.to_dict() == expected_dict


def test_schema_json_serialization(basic_schema):
    """Test JSON serialization and deserialization"""
    json_str = basic_schema.to_json()
    recreated_schema = ToolSchema.from_json(json_str)

    assert basic_schema.to_dict() == recreated_schema.to_dict()


def test_schema_to_file(basic_schema, tmp_path):
    schemafile = tmp_path / "schema.json"
    basic_schema.to_file(schemafile)
    schema_from_file = ToolSchema.from_file(schemafile)
    assert basic_schema == schema_from_file


def test_simple_function_schema(basic_generator):
    """Test schema generation for a simple function"""

    def test_func(a: int, b: str, c: float = 0.0) -> str:
        """Test function docstring"""
        return f"{a} {b} {c}"

    schema = basic_generator.generate_schema(test_func)

    assert schema.name == "test_func"
    assert schema.description == "Test function docstring"
    assert set([p.name for p in schema.parameters]) == {"a", "b", "c"}
    assert set(schema.required) == {"a", "b"}
    assert [p.param_type for p in schema.parameters if p.name == "a"] == ["integer"]
    assert [p.param_type for p in schema.parameters if p.name == "b"] == ["string"]
    assert [p.param_type for p in schema.parameters if p.name == "c"] == ["number"]


def test_method_schema(basic_generator):
    """Test schema generation for a class method"""

    class TestClass:
        def test_method(self, x: int) -> None:
            pass

    schema = basic_generator.generate_schema(TestClass().test_method)

    assert schema.name == "test_method"
    assert len(schema.parameters) == 1
    assert "self" not in schema.parameters


def test_unknown_type_handling(basic_generator):
    """Test handling of unknown type annotations"""
    from typing import Generic, TypeVar

    T = TypeVar("T")

    class GenericContainer(Generic[T]):
        def __init__(self, value: T):
            self.value = value

    def func_with_generic_type(x: GenericContainer[str], y: T, z: Any):
        pass

    schema = basic_generator.generate_schema(func_with_generic_type)
    assert [p.param_type for p in schema.parameters] == ["string", "string", "string"]


@patch("inspect.getsource")
def test_llm_failure_fallback(mock_getsource, llm_mock_generator, mock_llm):
    """Test fallback to basic schema when LLM fails"""

    def test_func(x: int) -> str:
        return str(x)

    mock_getsource.return_value = "def test_func(x: int) -> str: return str(x)"
    mock_llm.side_effect = Exception("LLM failed")

    schema = llm_mock_generator.generate_schema(test_func)

    # Should still get a valid basic schema
    assert isinstance(schema, ToolSchema)
    assert [p.name for p in schema.parameters] == ["x"]
    assert [p.param_type for p in schema.parameters] == ["integer"]


# Example of parametrized test
@pytest.mark.parametrize(
    "input_type,expected_type",
    [
        (int, {"type": "integer"}),
        (str, {"type": "string"}),
        (float, {"type": "number"}),
        (bool, {"type": "boolean"}),
        (list[int], {"type": "string"}),  # Complex types default to string
        (dict[str, int], {"type": "string"}),
        (Optional[int], {"type": "integer"}),
        (Union[str, None], {"type": "string"}),
    ],
)
def test_type_mapping(basic_generator, input_type, expected_type):
    """Test type mapping for different Python types"""

    def test_func(x: input_type):
        pass

    schema = basic_generator.generate_schema(test_func)
    logger.info(schema)
    assert schema.parameters[0].param_type == expected_type["type"]
