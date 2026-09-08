# 13. Architecture Decision Log

This chapter documents significant architecture decisions made during the development of the Studio application. Each decision follows the Architecture Decision Record (ADR) format.

## ADR-001: Microservices Architecture

**Date**: Inferred from codebase structure

**Status**: Accepted

**Context**: The system needs to handle multiple responsibilities including web serving, LLM inference, tool execution, and vector search. These have different scaling characteristics and resource requirements.

**Decision**: Decompose the system into four separate services:
1. **Backend** - Web API and frontend serving
2. **LLM Worker** - LLM inference and agent orchestration
3. **MCP Server** - Tool execution (paper search)
4. **Qdrant** - Vector database

**Consequences**:
- (+) Services can be scaled independently
- (+) LLM inference doesn't block web requests
- (+) Clear separation of concerns
- (-) More complex deployment
- (-) Inter-service communication overhead
- (-) Need to manage service startup order

## ADR-002: Pixi for Python Environment Management

**Date**: Inferred from `pyproject.toml`

**Status**: Accepted

**Context**: The project needs reproducible Python environments across Linux, macOS, and Windows. Traditional tools (pip, conda) have limitations with cross-platform reproducibility.

**Decision**: Use [Pixi](https://pixi.sh/) as the primary package manager with environment lockfiles.

**Consequences**:
- (+) Reproducible environments across platforms
- (+) Fast dependency resolution
- (+) Includes non-Python dependencies (Node.js, compilers)
- (-) Less familiar to developers used to pip/conda
- (-) Large Docker images when using Pixi base

**References**:
- [`pyproject.toml:75-108`](https://github.com/AIM-kennisplatformen/studio/blob/main/pyproject.toml#L75-L108)

## ADR-003: MCP Protocol for Tool Integration

**Date**: Inferred from codebase

**Status**: Accepted

**Context**: The LLM agent needs access to external tools (paper search). There are multiple approaches: function calling, LangChain tools, or standardized protocols.

**Decision**: Use the Model Context Protocol (MCP) with FastMCP server and mcp-use client library.

**Consequences**:
- (+) Standardized tool interface
- (+) Tools run in separate process (isolation)
- (+) SSE transport enables real-time updates
- (-) Additional service to maintain
- (-) Less mature than LangChain tools
- (-) Requires understanding MCP protocol

**References**:
- [`src/mcp_servers/main.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/mcp_servers/main.py)
- [`src/llm_worker/endpoints/ask.py:41-56`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/llm_worker/endpoints/ask.py#L41-L56)

## ADR-004: Socket.IO for Real-time Chat

**Date**: Inferred from codebase

**Status**: Accepted

**Context**: The chat interface requires real-time bidirectional communication for streaming LLM responses.

**Decision**: Use python-socketio with ASGI integration for WebSocket support.

**Alternatives Considered**:
- WebSockets directly (lower-level)
- Server-Sent Events (unidirectional)
- Long polling (inefficient)

**Consequences**:
- (+) Built-in reconnection and fallback
- (+) Room/namespace support for multi-user
- (+) Works with session middleware
- (-) Additional library dependency
- (-) Slightly more complex than raw WebSockets

**References**:
- [`src/backend/endpoints/chat.py:29-36`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/chat.py#L29-L36)

## ADR-005: In-Memory Knowledge Graph

**Date**: Inferred from codebase

**Status**: Accepted

**Context**: The knowledge graph data needs to be queryable for node context retrieval. Options include graph databases, JSON files, or in-memory structures.

**Decision**: Load knowledge graph from JSON file into memory at application startup.

**Consequences**:
- (+) Simple implementation
- (+) Fast queries (in-memory)
- (+) No additional database dependency
- (-) Data is read-only
- (-) Changes require restart
- (-) Limited scalability for large graphs

**References**:
- [`src/backend/utility/graph_data_loader.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/utility/graph_data_loader.py)

## ADR-006: Jotai for Frontend State Management

**Date**: Inferred from `package.json`

**Status**: Accepted

**Context**: The React frontend needs state management for chat messages, UI state, and graph navigation.

**Decision**: Use Jotai for atomic state management instead of Redux or Context API.

**Consequences**:
- (+) Minimal boilerplate
- (+) Atomic updates (fine-grained re-renders)
- (+) Works well with React 19
- (-) Less established than Redux
- (-) May need optics for complex state (jotai-optics included)

**References**:
- [`src/frontend/package.json:57`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/frontend/package.json#L57)
- [`src/frontend/src/data/atoms.js`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/frontend/src/data/atoms.js)

## ADR-007: shadcn/ui Component Library

**Date**: Inferred from `package.json`

**Status**: Accepted

**Context**: The frontend needs a consistent UI component library with AI-specific components.

**Decision**: Use shadcn/ui with Radix primitives and Tailwind CSS.

**Consequences**:
- (+) High-quality accessible components
- (+) Copy-paste pattern (own the code)
- (+) AI-specific components available (shadcn-io/ai)
- (+) Tailwind integration
- (-) Large number of component files to maintain

**References**:
- [`src/frontend/src/components/ui/`](https://github.com/AIM-kennisplatformen/studio/tree/main/src/frontend/src/components/ui)
- [`src/frontend/src/components/shadcn-io/ai/`](https://github.com/AIM-kennisplatformen/studio/tree/main/src/frontend/src/components/shadcn-io/ai)

## ADR-008: Qdrant for Vector Search

**Date**: Inferred from codebase

**Status**: Accepted

**Context**: The paper search feature needs semantic similarity search over document embeddings.

**Decision**: Use Qdrant as the vector database with Jina embeddings.

**Alternatives Considered**:
- Pinecone (managed, costly)
- Weaviate (more complex)
- Chroma (less mature)
- pgvector (requires PostgreSQL)

**Consequences**:
- (+) Excellent performance
- (+) Easy local deployment
- (+) Good filtering support (for Zotero hash matching)
- (+) Unprivileged container available
- (-) Additional service to operate
- (-) Data must be pre-ingested

**References**:
- [`docker-compose.yml:78-87`](https://github.com/AIM-kennisplatformen/studio/blob/main/docker-compose.yml#L78-L87)
- [`src/mcp_servers/lib/qdrant/qdrant_source.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/mcp_servers/lib/qdrant/qdrant_source.py)

## ADR-009: Optional OAuth Authentication

**Date**: Inferred from codebase

**Status**: Accepted

**Context**: The application may need user authentication, but should also work without it during development.

**Decision**: Implement OAuth (Authentik) with fallback defaults for local development.

**Consequences**:
- (+) Works out of the box for development
- (+) Production-ready authentication when configured
- (+) OpenID Connect standard
- (-) Default credentials in code (security risk if deployed without configuration)
- (-) Mixed authentication states to handle

**References**:
- [`src/backend/config.py:7-15`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/config.py#L7-L15)
- [`src/backend/endpoints/auth.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/auth.py)

## ADR-010: Streaming LLM Responses

**Date**: Inferred from codebase

**Status**: Accepted

**Context**: LLM responses can take several seconds. Users need feedback during generation.

**Decision**: Implement streaming using:
1. SSE from LLM Worker to Backend
2. Socket.IO from Backend to Frontend

**Consequences**:
- (+) Immediate feedback to users
- (+) Perceives faster response
- (+) Can show "thinking" indicators
- (-) More complex implementation
- (-) Need to handle partial responses

**References**:
- [`src/llm_worker/endpoints/ask.py:89-124`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/llm_worker/endpoints/ask.py#L89-L124)
- [`src/backend/endpoints/chat.py:144-182`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/chat.py#L144-L182)

## ADR-011: Prefetching Subnode Answers

**Date**: Inferred from codebase

**Status**: Accepted

**Context**: Users navigate between graph nodes expecting quick responses. Pre-computing answers for likely navigation paths improves perceived performance.

**Decision**: After answering the root question, prefetch answers for all subnodes ("Best practices", "Target groups", "Strategic overview") in background tasks.

**Consequences**:
- (+) Instant responses when user navigates
- (+) Better user experience
- (-) Increased LLM usage (wasted if user doesn't navigate)
- (-) Complexity in managing prefetch state
- (-) Memory usage for cached responses

**References**:
- [`src/backend/endpoints/graph.py:64-110`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/graph.py#L64-L110)
- [`src/backend/endpoints/chat.py:203-211`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/chat.py#L203-L211)

## Decision Template

For future decisions, use this template:

```markdown
## ADR-NNN: Title

**Date**: YYYY-MM-DD

**Status**: Proposed | Accepted | Deprecated | Superseded

**Context**: What is the issue or problem we are facing?

**Decision**: What is the decision we made?

**Alternatives Considered**: (optional)
- Option A
- Option B

**Consequences**:
- (+) Positive consequence
- (-) Negative consequence

**References**:
- Link to relevant code or documentation
```
