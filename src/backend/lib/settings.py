import tomllib
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class ClientType(str, Enum):
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class ModelType(str, Enum):
    HAIKU = "claude-3-haiku-20240307"
    LLAMA31 = "llama3.1"
    QWEN2 = "qwen2.5:7b-instruct-fp16"
    QWEN3 = "qwen3:8b-q8_0"
    CODELLAMA34B = "codellama:34b"
    PHI3 = "phi3:latest"


class ModelConfig(BaseModel):
    client_type: ClientType
    model_type: ModelType
    host: Optional[HttpUrl] = HttpUrl("http://localhost:11434")
    allowed_tools: Optional[List[str]] = None
    max_tokens: int = 1000

    def __str__(self):
        return f"client_type={self.client_type.value}\nmodel_type={self.model_type.value}\ntools={self.allowed_tools}\nhost={self.host}\nmax_tokens={self.max_tokens}"

    @classmethod
    def from_toml(cls, path: Path):
        with path.open("rb") as f:
            config = tomllib.load(f)["llm"]

        return cls(**config)
