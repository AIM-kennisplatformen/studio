import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("MCP_TOOL_CONFIG_PATH", "/tmp/mcp-tool-config.json")
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("OPENAI_HOST", "http://localhost:11434/v1")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
