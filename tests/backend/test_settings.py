from itertools import product
from typing import List

import pytest
from pydantic import HttpUrl

from llm_tooluse.settings import ClientType, ModelConfig, ModelType


def generate_model_configs() -> List[ModelConfig]:
    """
    Generate all possible combinations of ModelConfig.
    Returns a list of ModelConfig instances with all valid combinations.
    """
    # Define possible values for each parameter
    client_types = list(ClientType)
    model_types = list(ModelType)
    hosts = [
        HttpUrl("http://localhost:11434"),  # Default Ollama host
    ]
    tools_options = [
        None,
    ]
    max_tokens_options = [1000]  # Example token limits

    # Generate all combinations
    configs = []
    for client, model, host, tools, max_tokens in product(
        client_types, model_types, hosts, tools_options, max_tokens_options
    ):
        # Skip invalid combinations
        if client == ClientType.ANTHROPIC and host == HttpUrl("http://localhost:11434"):
            continue
        if client == ClientType.OLLAMA and host != HttpUrl("https://localhost:11434"):
            continue
        if client == ClientType.OLLAMA and model == ModelType.HAIKU:
            continue
        if client == ClientType.ANTHROPIC and model == ModelType.LLAMA31:
            continue

        configs.append(
            ModelConfig(
                client_type=client,
                model_type=model,
                host=host,
                allowed_tools=tools,
                max_tokens=max_tokens,
            )
        )
    print(configs)
    return configs


@pytest.fixture(params=generate_model_configs())
def model_config(request) -> ModelConfig:
    """
    Pytest fixture that yields each possible ModelConfig combination.
    """
    return request.param


def test_model_config_str_representation(model_config):
    """Test that string representation contains all necessary information."""
    str_repr = str(model_config)
    assert model_config.client_type.value in str_repr
    assert model_config.model_type.value in str_repr
    assert str(model_config.host) in str_repr
    assert str(model_config.max_tokens) in str_repr
    if model_config.allowed_tools:
        assert str(model_config.allowed_tools) in str_repr


def test_model_config_properties(model_config):
    """Test that all ModelConfig properties are set correctly."""
    assert isinstance(model_config.client_type, ClientType)
    assert isinstance(model_config.model_type, ModelType)
    assert isinstance(model_config.host, HttpUrl)
    assert isinstance(model_config.max_tokens, int)
    if model_config.allowed_tools is not None:
        assert isinstance(model_config.allowed_tools, list)
        assert all(isinstance(tool, str) for tool in model_config.allowed_tools)


# Example of how to use generate_model_configs() directly in other tests
def test_batch_processing():
    """Example test showing how to use all config combinations directly."""
    configs = generate_model_configs()
    for config in configs:
        # Your test logic here
        assert isinstance(config, ModelConfig)
        # Process each config as needed


def test_from_toml(tmp_path):
    """Test loading ModelConfig from TOML file."""
    # Create a temporary TOML file
    config_path = tmp_path / "config.toml"
    toml_content = """
    [llm]
    client_type = "ollama"
    model_type = "llama3.1"
    allowed_tools = ["tool1", "tool2"]
    max_tokens = 2000
    """
    config_path.write_text(toml_content)

    config = ModelConfig.from_toml(config_path)
    assert config.client_type == ClientType.OLLAMA
    assert config.model_type == ModelType.LLAMA31
    assert config.host == HttpUrl("http://localhost:11434")
    assert config.allowed_tools == ["tool1", "tool2"]
    assert config.max_tokens == 2000
