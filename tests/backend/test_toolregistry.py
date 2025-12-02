import pytest

from llm_tooluse.calculator import add, subtract
from llm_tooluse.schemagenerators import ToolSchema
from llm_tooluse.tools import Tool, ToolCollection, ToolFactory, ToolRegistry


# Test fixtures
@pytest.fixture
def add_tool(basic_generator):
    return Tool.from_function(add, basic_generator)


@pytest.fixture
def subtract_tool(basic_generator):
    return Tool.from_function(subtract, basic_generator)


@pytest.fixture
def empty_registry():
    # Create a new registry instance for testing
    registry = ToolRegistry()
    registry._tools = {}  # Clear any existing tools
    registry.initialized = True
    return registry


@pytest.fixture
def tool_factory(basic_generator):
    return ToolFactory(schema_generator=basic_generator)


# Tests for Tool class
class TestTool:
    def test_create_tool_from_fun_and_schema(self, basic_generator):
        """Test creating a tool from a function with a schema generator"""
        tool = Tool.from_function(add, basic_generator)

        assert tool.func == add
        assert tool.schema.name == "add"
        assert [p.name for p in tool.schema.parameters] == ["x", "y"]
        assert "x" in tool.schema.required
        assert "y" in tool.schema.required

    def test_create_tool_from_fun_only(self):
        """Test creating a tool from a function with a schema generator"""
        tool = Tool.from_function(add)

        assert tool.func == add
        assert tool.schema.name == "add"
        assert [p.name for p in tool.schema.parameters] == ["x", "y"]
        assert "x" in tool.schema.required
        assert "y" in tool.schema.required

    def test_create_tool_from_schema_dict(self):
        """Test creating a tool from a function and a schema dictionary"""

        tool = Tool.from_function(add)
        generated_dict = tool.schema.to_dict()
        tool_from_schema = tool.from_schema_dict(add, generated_dict)
        assert generated_dict == tool_from_schema.schema.to_dict()

        d = {
            "name": "add",
            "description": "Add x plus y",
            "parameters": [
                {
                    "name": "x",
                    "param_type": "number",
                    "description": None,
                    "enum": None,
                    "nullable": None,
                },
                {
                    "name": "y",
                    "param_type": "number",
                    "description": None,
                    "enum": None,
                    "nullable": None,
                },
            ],
            "required": ["x", "y"],
        }

        tool_from_d = tool.from_schema_dict(add, d)
        assert tool_from_d.schema.name == "add"
        assert tool_from_d.schema.description == "Add x plus y"
        assert len(tool_from_d.schema.parameters) == 2
        assert tool_from_d.schema.required == ["x", "y"]

    def test_get_schema(self, add_tool):
        """Test getting schema in different formats"""
        schema_dict = add_tool.get_schema_fmt(format="dict")
        schema_json = add_tool.get_schema_fmt(format="json")

        assert isinstance(schema_dict, dict)
        assert schema_dict["name"] == "add"

        assert isinstance(schema_json, str)
        assert "add" in schema_json

    def test_update_schema(self, add_tool):
        """Test updating schema from JSON"""
        new_schema = {
            "name": "updated_add",
            "description": "Subtract num1 from num2",
            "parameters": [
                {
                    "name": "num1",
                    "param_type": "number",
                    "description": None,
                    "enum": None,
                    "nullable": None,
                },
                {
                    "name": "num2",
                    "param_type": "number",
                    "description": None,
                    "enum": None,
                    "nullable": None,
                },
            ],
            "required": ["num1", "num2"],
        }

        import json

        add_tool.update_schema(json.dumps(new_schema))

        assert add_tool.schema.name == "updated_add"
        assert "num1" in add_tool.schema.required
        assert "num2" in add_tool.schema.required

    def test_tool_callable(self, add_tool):
        """Test that tool is callable like the original function"""
        result = add_tool(3, 4)
        assert result == 7

    def test_tool_name(self, add_tool):
        """Test tool name property"""
        assert add_tool.__name__() == "add"

    def test_tool_str_repr(self, add_tool):
        """Test string and repr representations"""
        assert str(add_tool) == "add"
        assert repr(add_tool) == "add"

    def test_tool_equality(self, basic_generator):
        """Test equality comparison between tools"""
        tool1 = Tool.from_function(add, basic_generator)
        tool2 = Tool.from_function(add, basic_generator)
        tool3 = Tool.from_function(subtract, basic_generator)

        assert tool1 == tool2
        assert tool1 != tool3

    def test_compatible_schema(self, basic_generator):
        """Test schema compatibility check"""
        tool1 = Tool.from_function(add, basic_generator)
        tool2 = Tool.from_function(add, basic_generator)
        tool3 = Tool.from_function(subtract, basic_generator)

        assert tool1.has_compatible_schema(tool2)
        # add and subtract have the same parameter structure
        assert tool1.has_compatible_schema(tool3)

    def test_tool_hash(self, basic_generator):
        """Test tool hash functionality"""
        tool1 = Tool.from_function(add, basic_generator)
        tool2 = Tool.from_function(add, basic_generator)

        assert hash(tool1) == hash(tool2)

        # Tools should be usable in native sets
        tool_set = {tool1, tool2}
        assert len(tool_set) == 1


# Tests for ToolRegistry class
class TestToolRegistry:
    def test_registry_singleton(self):
        """Test that ToolRegistry is a singleton"""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()

        assert registry1 is registry2

    def test_register_tool(self, add_tool):
        """Test registering a tool"""
        registry = ToolRegistry()
        assert len(registry.available_tools) == 0

        registry.register(add_tool)

        assert len(registry.available_tools) == 1
        assert "add" in registry.available_tools
        assert registry.get("add") == add_tool

    def test_register_multiple_tools(self, empty_registry, add_tool, subtract_tool):
        """Test registering multiple tools"""
        empty_registry.register(add_tool)
        assert len(empty_registry.available_tools) == 1
        assert "add" in empty_registry.available_tools

        empty_registry.register(subtract_tool)
        assert "subtract" in empty_registry.available_tools
        assert len(empty_registry.available_tools) == 2

    def test_register_duplicates(self, empty_registry, add_tool):
        """Test registering multiple tools"""
        empty_registry.register(add_tool)
        empty_registry.register(add_tool)
        assert len(empty_registry.available_tools) == 1
        assert "add" in empty_registry.available_tools

    def test_get_nonexistent_tool(self, empty_registry):
        """Test getting a tool that doesn't exist"""
        with pytest.raises(ValueError):
            empty_registry.get("nonexistent")

    def test_available_tools(self, empty_registry, add_tool, subtract_tool):
        """Test getting available tools"""
        empty_registry.register(add_tool)
        empty_registry.register(subtract_tool)

        available = empty_registry.available_tools
        assert available == {"add", "subtract"}


# Tests for ToolCollection class
class TestToolCollection:
    def test_create_from_tools(self, add_tool, subtract_tool):
        """Test creating a collection from tools"""
        collection = ToolCollection.from_tools([add_tool, subtract_tool])

        assert "add" in collection.tool_names
        assert "subtract" in collection.tool_names

    def test_get_functions(self, add_tool, subtract_tool):
        """Test getting functions from a collection"""
        collection = ToolCollection.from_tools([add_tool, subtract_tool])
        functions = collection.get_functions()

        assert len(functions) == 2
        assert add_tool in functions
        assert subtract_tool in functions

    def test_get_schemas(self, add_tool, subtract_tool):
        """Test getting schemas from a collection"""
        collection = ToolCollection.from_tools([add_tool, subtract_tool])
        schemas = collection.get_schemas()

        assert len(schemas) == 2
        assert all(isinstance(schema, ToolSchema) for schema in schemas)
        assert all(hasattr(s, "name") for s in schemas)
        assert any(schema.name == "add" for schema in schemas)
        assert any(schema.name == "subtract" for schema in schemas)

    def test_call_tool(self, add_tool, subtract_tool):
        """Test calling a tool from the collection"""
        collection = ToolCollection.from_tools([add_tool, subtract_tool])

        result_add = collection("add", x=5, y=3)
        result_subtract = collection("subtract", x=10, y=4)

        assert result_add == 8
        assert result_subtract == 6

    def test_call_nonexistent_tool(self, add_tool):
        """Test calling a tool that doesn't exist in the collection"""
        collection = ToolCollection.from_tools([add_tool])

        with pytest.raises(ValueError):
            collection("nonexistent", x=1, y=2)

    def test_contains(self, add_tool, subtract_tool):
        """Test contains operator"""
        collection = ToolCollection.from_tools([add_tool, subtract_tool])

        assert "add" in collection
        assert "subtract" in collection
        assert "nonexistent" not in collection

    def test_combine_collections(self, add_tool, subtract_tool):
        """Test combining tool collections"""
        collection1 = ToolCollection.from_tools([add_tool])
        collection2 = ToolCollection.from_tools([subtract_tool])

        combined = collection1 * collection2

        assert "add" in combined
        assert "subtract" in combined
        assert len(combined.tool_names) == 2

    def test_subtract_collections(self, add_tool, subtract_tool):
        """Test subtracting tool collections"""
        collection1 = ToolCollection.from_tools([add_tool, subtract_tool])
        collection2 = ToolCollection.from_tools([subtract_tool])

        result = collection1 - collection2

        assert "add" in result
        assert "subtract" not in result
        assert len(result.tool_names) == 1

    def test_subtract_by_names(self, add_tool, subtract_tool):
        """Test subtracting tools by name"""
        collection = ToolCollection.from_tools([add_tool, subtract_tool])

        result1 = collection - {"subtract"}
        result2 = collection - ["subtract"]

        assert "add" in result1
        assert "subtract" not in result1

        assert "add" in result2
        assert "subtract" not in result2

    def test_subtract_typeerror(self, add_tool):
        """Test subtracting with invalid type"""
        collection = ToolCollection.from_tools([add_tool])
        with pytest.raises(TypeError):
            new_collection = collection - "unsupported_type"

    def test_str_repr(self, add_tool, subtract_tool):
        """Test string and repr representations"""
        collection = ToolCollection.from_tools([add_tool, subtract_tool])

        str_rep = str(collection)
        repr_rep = repr(collection)

        assert "add" in str_rep
        assert "subtract" in str_rep
        assert "add" in repr_rep
        assert "subtract" in repr_rep


# Tests for ToolFactory class
class TestToolFactory:
    def test_create_tool(self, tool_factory):
        """Test creating a tool with factory"""
        tool = tool_factory.create_tool(add)

        assert tool.func == add
        assert tool.schema.name == "add"

    def test_create_collection(self, tool_factory):
        """Test creating a tool collection with factory"""
        collection = tool_factory.create_collection([add, subtract])

        assert isinstance(collection, ToolCollection)
        assert len(collection.tool_names) == 2
        assert "add" in collection
        assert "subtract" in collection

        # Test calling tools from the collection
        assert collection("add", x=5, y=3) == 8
        assert collection("subtract", x=10, y=4) == 6
