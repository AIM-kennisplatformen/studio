# 5. Principles

This chapter documents the architecture and design principles that guide development of the Studio application. These principles are inferred from the codebase patterns and tooling choices.

## 5.1 Architecture Principles

### 5.1.1 Service Separation

**Principle**: Separate concerns into distinct services with clear responsibilities.

**Evidence**:
- Backend API handles web serving and authentication
- LLM Worker handles inference (isolated from web requests)
- MCP Server handles tool execution
- Qdrant handles vector storage

**Benefits**:
- Independent scaling
- Fault isolation
- Clear ownership
- Technology flexibility per service

### 5.1.2 Configuration Over Code

**Principle**: Externalize configuration via environment variables and config files.

**Evidence**:
- All service URLs configurable via `.env`
- LLM settings in `llm_worker_config.toml`
- OAuth credentials in environment variables
- Vite build-time configuration

**Implementation**:
```python
# src/backend/config.py
load_dotenv()
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:10090")
```

### 5.1.3 Async-First Design

**Principle**: Use asynchronous programming for I/O operations.

**Evidence**:
- All FastAPI endpoints use `async def`
- httpx for async HTTP client
- python-socketio in async mode
- asyncio tasks for prefetching

**Benefits**:
- Better resource utilization
- Higher concurrency
- Non-blocking I/O

### 5.1.4 Streaming by Default

**Principle**: Stream long-running operations to provide immediate feedback.

**Evidence**:
- LLM responses streamed via SSE
- WebSocket for real-time client updates
- Event-based architecture for progress updates

**Benefits**:
- Perceived performance improvement
- Early error detection
- Better user experience

## 5.2 Design Principles

### 5.2.1 Protocol Standardization

**Principle**: Use standard protocols and APIs for interoperability.

**Evidence**:
- OpenAI-compatible API for LLM (works with Ollama, OpenAI, Nebius)
- MCP protocol for tool integration
- OpenID Connect for authentication
- Socket.IO for WebSocket (with fallback)

### 5.2.2 Explicit Over Implicit

**Principle**: Make dependencies and data flow explicit.

**Evidence**:
- Pydantic models for API contracts
- Type hints throughout Python code
- Explicit router registration in main.py
- Clear import structure

```python
# Explicit model definitions
class ContextResponse(BaseModel):
    message: Optional[str] = None
    nodes: List[Node] = []
    edges: List[Edge] = []
```

### 5.2.3 Fail Gracefully

**Principle**: Handle errors gracefully with meaningful feedback.

**Evidence**:
- Error responses include error codes
- Socket.IO emits error messages to client
- LLM unavailable doesn't crash the application

```python
# src/backend/endpoints/chat.py:135-141
if resp.status_code != 200:
    await sio.emit(
        "message",
        {"role": "chatbot", "content": "❌ Error: worker unavailable"},
        to=sid,
    )
```

### 5.2.4 Reproducible Environments

**Principle**: Development and deployment environments should be reproducible.

**Evidence**:
- Pixi lockfiles for Python dependencies
- package-lock.json for Node dependencies
- Docker Compose for service orchestration
- Platform-specific task definitions in pyproject.toml

## 5.3 Code Conventions

### 5.3.1 Python Conventions

**Linting**: Ruff with selected rules

```toml
# pyproject.toml
[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "C4", "PT"]
```

**Type Checking**: Mypy with permissive settings

```toml
# pyproject.toml
[tool.mypy]
allow_redefinition = true
```

**Logging**: Loguru for structured logging

```python
from loguru import logger
logger.info(f"Starting worker on http://0.0.0.0:{port}")
```

### 5.3.2 JavaScript/React Conventions

**Component Structure**: Function components with hooks

**State Management**: Jotai atoms for global state

```javascript
// Atomic state
export const messagesAtom = atom([]);
export const textStatusAtom = atom("idle");
```

**Styling**: Tailwind CSS with shadcn/ui components

**Path Aliases**: `@/` for src directory

```javascript
import { Button } from "@/components/ui/button";
```

### 5.3.3 API Conventions

**Response Format**: Consistent JSON structure

```json
{
  "message": "Description",
  "data": {},
  "error": null
}
```

**Error Handling**: HTTP status codes + error field in response

**Authentication**: Session cookies for web, connection validation for WebSocket

## 5.4 Testing Principles

### 5.4.1 Test Structure

- Tests in `tests/` directory
- Mirror source structure (`tests/backend/`)
- pytest as test framework

### 5.4.2 Test Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["client", "server"]
addopts = ["--import-mode=importlib"]
```

## 5.5 Documentation Principles

### 5.5.1 Code Documentation

- Docstrings for public functions
- Type hints for function signatures
- Inline comments for complex logic

### 5.5.2 API Documentation

- FastAPI auto-generates OpenAPI docs
- Available at `/docs` endpoint

## 5.6 Security Principles

### 5.6.1 Defense in Depth

- Session middleware with signed cookies
- CORS restricted to known origins
- WebSocket authentication validates session

### 5.6.2 Secrets Management

- No secrets in code (except development defaults)
- Environment variables for sensitive config
- `.env` file excluded from version control

## 5.7 Principle Violations and Technical Debt

| Violation | Principle | Impact | Recommendation |
|-----------|-----------|--------|----------------|
| Default OAuth credentials in code | Secrets Management | Security risk if deployed without config | Remove defaults, require explicit configuration |
| In-memory session storage | Data Persistence | Data loss on restart | Add Redis or database backend |
| Hardcoded subnode names | Configuration Over Code | Inflexible graph structure | Make configurable |
| Mixed relative/absolute imports | Explicit Over Implicit | Import confusion | Standardize import style |
