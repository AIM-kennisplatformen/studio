"""Configure pytest"""

from unittest.mock import Mock

import pytest
from _pytest.logging import LogCaptureFixture
from loguru import logger

from llm_tooluse.llm import LLMClient
from llm_tooluse.schemagenerators import (
    BasicSchemaGenerator,
    LLMSchemaGenerator,
    ParameterSchema,
    ToolSchema,
)
from llm_tooluse.settings import ClientType, ModelConfig, ModelType


@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    """Override pytest's caplog fixture to work with loguru."""
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,  # Set to False since we're not using multiprocessing in tests
    )
    yield caplog
    logger.remove(handler_id)


@pytest.fixture(autouse=True)
def propagate_logs():
    """Fixture to handle --log-cli-level flag with loguru."""
    import logging

    class PropagateHandler(logging.Handler):
        def emit(self, record):
            if logging.getLogger(record.name).isEnabledFor(record.levelno):
                logging.getLogger(record.name).handle(record)

    logger.remove()
    logger.add(PropagateHandler(), format="{message}")
    return


@pytest.fixture
def basic_schema():
    param1 = ParameterSchema(name="param1", param_type="string")
    return ToolSchema(
        name="test_function",
        description="A test function",
        parameters=[param1],
        required=["param1"],
    )


@pytest.fixture
def basic_generator():
    return BasicSchemaGenerator()


@pytest.fixture
def mock_llm():
    return Mock()


@pytest.fixture
def llm_mock_generator(mock_llm):
    return LLMSchemaGenerator(mock_llm)


@pytest.fixture
def ollama_config_phi() -> ModelConfig:
    """Create a ModelConfig for local Ollama"""
    config = ModelConfig(
        client_type=ClientType.OLLAMA,
        model_type=ModelType.PHI3,
        max_tokens=1000,
    )
    logger.info("Created Ollama config")
    return config


@pytest.fixture
def phi_llm(ollama_config_phi):
    llm = LLMClient(ollama_config_phi)
    return llm
