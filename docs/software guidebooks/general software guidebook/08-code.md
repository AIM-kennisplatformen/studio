# 8. Code

This chapter describes the code organization, patterns, and conventions used in the Studio application.

## 8.1 Project Structure

```
studio/
├── src/
│   ├── backend/           # FastAPI backend API
│   │   ├── endpoints/     # API route handlers
│   │   └── utility/       # Shared utilities and models
│   ├── frontend/          # React SPA
│   │   └── src/
│   │       ├── components/  # React components
│   │       ├── data/        # State management and API calls
│   │       └── knowledge-graph/  # Graph data
│   ├── llm_worker/        # LLM inference service
│   │   └── endpoints/     # Worker API routes
│   └── mcp_servers/       # MCP tool servers
│       ├── lib/           # Data source integrations
│       └── tools/         # MCP tool definitions
├── tests/                 # Test files
├── dockerfiles/           # Docker build definitions
├── docs/                  # Documentation
└── .github/workflows/     # CI/CD pipelines
```

## 8.2 Backend Code Organization

### 8.2.1 Entry Point

The backend entry point is [`src/backend/main.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/main.py). It:

1. Creates the FastAPI application with lifespan management
2. Loads the knowledge graph at startup
3. Configures middleware (Session, CORS)
4. Mounts routers for different API domains

```python
# src/backend/main.py:29-56
app = FastAPI(
    title="Knowledge Graph API",
    description="API for chat-based knowledge graph generation",
    version="0.1.0",
    lifespan=lifespan,
)
```

### 8.2.2 Router Structure

| Router | Module | Prefix | Purpose |
|--------|--------|--------|---------|
| `auth_router` | [`endpoints/auth.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/auth.py) | `/auth/*` | OAuth authentication |
| `chat_router` | [`endpoints/chat.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/chat.py) | (none) | Chat-related utilities |
| `graph_router` | [`endpoints/graph.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/graph.py) | `/nodes/*` | Knowledge graph API |
| `asset_router` | [`endpoints/assets.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/assets.py) | `/assets/*` | Static file serving |
| `frontend` | [`endpoints/assets.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/assets.py) | `/app` | SPA entry point |

### 8.2.3 Socket.IO Integration

WebSocket communication uses python-socketio mounted as an ASGI app:

```python
# src/backend/endpoints/chat.py:29-36
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[BASE_URL],
)
socket_app = socketio.ASGIApp(sio)

# src/backend/main.py:51
app.mount("/socket.io", socket_app)
```

## 8.3 Frontend Code Organization

### 8.3.1 Entry Point

The React application starts at [`src/frontend/src/main.jsx`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/frontend/src/main.jsx), rendering the root `App` component.

### 8.3.2 Main Components

| Component | File | Purpose |
|-----------|------|---------|
| `App` | [`App.jsx`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/frontend/src/App.jsx) | Root layout with resizable panels |
| `Chat` | [`chat.jsx`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/frontend/src/chat.jsx) | Chat interface with message history |
| `Graph` | [`graph.jsx`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/frontend/src/graph.jsx) | Knowledge graph visualization |

### 8.3.3 State Management

The frontend uses [Jotai](https://jotai.org/) for atomic state management:

```javascript
// src/frontend/src/data/atoms.js
export const messagesAtom = atom([]);
export const textAtom = atom("");
export const textStatusAtom = atom("idle");
export const centerNodeAtom = atom(1);
```

### 8.3.4 Component Library

UI components are built with [shadcn/ui](https://ui.shadcn.com/), located in:

- `src/frontend/src/components/ui/` - Base shadcn components
- `src/frontend/src/components/shadcn-io/ai/` - AI chat components

### 8.3.5 Graph Visualization

The knowledge graph is rendered using [@xyflow/react](https://reactflow.dev/) (React Flow):

```javascript
// src/frontend/src/App.jsx:60-64
<ReactFlowProvider>
  <Graph data={data} width={leftWidth} />
</ReactFlowProvider>
```

## 8.4 LLM Worker Code Organization

### 8.4.1 Entry Point

[`src/llm_worker/main.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/llm_worker/main.py) creates a FastAPI app with a single router for LLM inference.

### 8.4.2 Agent Pattern

The worker uses the MCP-Use library to create LangChain agents with MCP tool access:

```python
# src/llm_worker/endpoints/ask.py:41-56
async def create_agent() -> MCPAgent:
    config = load_config_file(os.getenv("MCP_TOOL_CONFIG_PATH"))
    client = MCPClient(config)
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        base_url=os.getenv("OPENAI_HOST"),
    )
    return MCPAgent(
        llm=llm,
        client=client,
        max_steps=30,
        callbacks=[CallbackHandler()],
    )
```

## 8.5 MCP Server Code Organization

### 8.5.1 Entry Point

[`src/mcp_servers/main.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/mcp_servers/main.py) starts the MCP server using FastMCP:

```python
from mcp_servers.tools.scepa_paper_search import mcp

if __name__ == "__main__":
    mcp.settings.host = "0.0.0.0"
    mcp.run(transport="sse")
```

### 8.5.2 Tool Definition

MCP tools are defined using the `@mcp.tool()` decorator:

```python
# src/mcp_servers/tools/scepa_paper_search.py:24-27
@mcp.tool()
@observe(name="get_literature_supported_knowledge_sources")
async def get_literature_supported_knowledge(
    full_question: str, keywords_related_to_question: str
) -> str:
```

### 8.5.3 Data Source Pattern

External data sources are encapsulated in classes:

| Class | File | Purpose |
|-------|------|---------|
| `QdrantSource` | [`lib/qdrant/qdrant_source.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/mcp_servers/lib/qdrant/qdrant_source.py) | Vector similarity search |
| `ZoteroSource` | [`lib/zotero/zotero_source.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/mcp_servers/lib/zotero/zotero_source.py) | Bibliography metadata |

## 8.6 Code Patterns

### 8.6.1 Configuration via Environment Variables

All services load configuration from environment variables using `python-dotenv`:

```python
# src/backend/config.py
load_dotenv()
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:10090")
```

### 8.6.2 Pydantic Models for API Contracts

Request and response schemas use Pydantic:

```python
# src/backend/utility/graph_api_models.py
class ContextResponse(BaseModel):
    message: Optional[str] = None
    nodes: List[Node] = []
    edges: List[Edge] = []
    sources: List[Source] = []
    error: Optional[str] = None
```

### 8.6.3 Async-First Design

All I/O operations use async/await:

```python
# src/backend/endpoints/chat.py:124-133
async with httpx.AsyncClient(timeout=None) as client:
    async with client.stream(
        "POST",
        f"{worker_url}/ask_stream",
        json={...},
    ) as resp:
        async for line in resp.aiter_lines():
            ...
```

### 8.6.4 Streaming Responses

LLM responses are streamed using Server-Sent Events (SSE):

```python
# src/llm_worker/endpoints/ask.py:117-123
return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    },
)
```

## 8.7 Import Conventions

### 8.7.1 Backend Imports

Backend modules use relative imports within the package:

```python
# src/backend/endpoints/chat.py
from backend.config import LLM_WORKER_URL, LLM_WORKER_PORT
from backend.endpoints.graph import user_graph_contexts
```

### 8.7.2 Frontend Path Aliases

The frontend uses Vite path aliases for cleaner imports:

```javascript
// vite.config.js
resolve: {
  alias: {
    "@": path.resolve(__dirname, "./src"),
  },
}

// Usage in components
import { Button } from "@/components/ui/button";
```

## 8.8 Testing

### 8.8.1 Test Structure

Tests are located in the `tests/` directory:

```
tests/
└── backend/
    ├── __init__.py
    ├── conftest.py
    ├── test_llmschema_integration.py
    ├── test_schemagenerators.py
    ├── test_settings.py
    └── test_toolregistry.py
```

### 8.8.2 Test Framework

- **Framework**: pytest
- **Configuration**: [`pyproject.toml`](https://github.com/AIM-kennisplatformen/studio/blob/main/pyproject.toml#L68-L70)

```toml
[tool.pytest.ini_options]
pythonpath = ["client", "server"]
addopts = ["--import-mode=importlib"]
```

## 8.9 Linting and Type Checking

### 8.9.1 Ruff

Python linting uses Ruff with selected rules:

```toml
# pyproject.toml
[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "C4", "PT"]
```

### 8.9.2 Mypy

Type checking configuration allows some flexibility:

```toml
# pyproject.toml
[tool.mypy]
allow_redefinition = true
disable_error_code = ["call-arg", "import-untyped", ...]
```

### 8.9.3 ESLint

Frontend linting uses ESLint with React plugins:

```javascript
// eslint.config.js
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
```
