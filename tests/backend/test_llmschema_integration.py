import pytest
from loguru import logger

from llm_tooluse.calculator import add
from llm_tooluse.schemagenerators import (
    BasicSchemaGenerator,
    LLMSchemaGenerator,
    ToolSchema,
)


@pytest.fixture
def basic_generator():
    basic_generator = BasicSchemaGenerator()
    return basic_generator


@pytest.fixture
def llm_generator_phi(phi_llm):
    """Create LLMSchemaGenerator with Ollama client"""
    try:
        generator = LLMSchemaGenerator(phi_llm)
        logger.success("Successfully created LLM generator")
    except Exception as e:
        logger.error(f"Failed to create LLM generator: {e}")
        raise
    return generator


@pytest.mark.integration
def test_basic_schema_generation(basic_generator):
    """Test generating schema for a simple function with Ollama"""
    basic_schema = basic_generator.generate_schema(add)
    assert isinstance(basic_schema, ToolSchema), (
        f"Expected ToolSchema but got {type(basic_schema)}"
    )


@pytest.mark.integration
def test_llm_integration(llm_generator_phi, basic_generator):
    llm_schema = llm_generator_phi.generate_schema(add)
    assert isinstance(llm_schema, ToolSchema)
