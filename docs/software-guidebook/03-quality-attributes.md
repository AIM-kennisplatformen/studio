# 3. Quality Attributes

This chapter describes the non-functional requirements and quality attributes that shape the architecture of the Studio application.

## 3.1 Overview

Quality attributes define how the system should behave beyond its functional requirements. They influence architectural decisions and trade-offs.

## 3.2 Quality Attribute Scenarios

### 3.2.1 Responsiveness

**Priority**: High

**Scenario**: When a user sends a chat message, they should see the AI response begin streaming within 2 seconds, with continuous token updates until completion.

**Measure**: Time to first token < 2 seconds (dependent on LLM provider)

**Implementation**:
- Streaming responses via Server-Sent Events ([`src/llm_worker/endpoints/ask.py:89-124`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/llm_worker/endpoints/ask.py#L89-L124))
- Socket.IO for real-time client updates ([`src/backend/endpoints/chat.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/chat.py))
- "Thinking" indicator in UI while waiting

### 3.2.2 Perceived Performance (Prefetching)

**Priority**: High

**Scenario**: After answering a root question, when the user clicks a subnode (Best practices, Target groups, Strategic overview), the answer should appear instantly.

**Measure**: Time to display prefetched answer < 100ms

**Implementation**:
- Background prefetching of subnode answers ([`src/backend/endpoints/chat.py:203-211`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/chat.py#L203-L211))
- In-memory cache per user ([`src/backend/endpoints/graph.py:52-57`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/graph.py#L52-L57))

### 3.2.3 Usability

**Priority**: High

**Scenario**: A researcher with no technical background should be able to explore the knowledge graph and ask questions without training.

**Measures**:
- Time to first successful question < 1 minute
- No technical jargon in UI
- Clear visual feedback during operations

**Implementation**:
- Intuitive split-panel layout ([`src/frontend/src/App.jsx`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/frontend/src/App.jsx))
- Standard chat interface patterns
- shadcn/ui for accessible components

### 3.2.4 Flexibility (LLM Provider)

**Priority**: Medium

**Scenario**: The system should work with different LLM providers (Ollama local, OpenAI cloud, Nebius) without code changes.

**Measure**: Switching providers requires only configuration changes

**Implementation**:
- OpenAI-compatible API abstraction
- Configuration via environment variables and TOML files
- MCP protocol for tool integration

### 3.2.5 Deployability

**Priority**: Medium

**Scenario**: A developer should be able to run the full system locally within 15 minutes of cloning the repository.

**Measures**:
- Setup time < 15 minutes
- Minimal external dependencies
- Clear documentation

**Implementation**:
- Pixi for reproducible environments
- Docker Compose for full stack
- Sample configuration files provided
- Comprehensive README

### 3.2.6 Observability

**Priority**: Medium

**Scenario**: Operations staff should be able to trace LLM requests to understand performance and debug issues.

**Measure**: All LLM calls traceable via Langfuse

**Implementation**:
- Langfuse integration ([`src/llm_worker/endpoints/ask.py:22-26`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/llm_worker/endpoints/ask.py#L22-L26))
- Langfuse callbacks on agent ([`src/llm_worker/endpoints/ask.py:55`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/llm_worker/endpoints/ask.py#L55))

### 3.2.7 Security

**Priority**: Medium

**Scenario**: Only authenticated users should access the application when OAuth is configured.

**Measures**:
- Unauthenticated requests redirected to login
- Session cookies signed and secure
- CORS restricted to known origins

**Implementation**:
- OAuth flow via Authentik ([`src/backend/endpoints/auth.py`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/auth.py))
- Session middleware with secret key ([`src/backend/main.py:36-41`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/main.py#L36-L41))
- CORS configuration ([`src/backend/main.py:43-49`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/main.py#L43-L49))

## 3.3 Quality Attribute Trade-offs

| Trade-off | Decision | Rationale |
|-----------|----------|-----------|
| Simplicity vs. Persistence | In-memory sessions | Simpler implementation, acceptable for demo/research use |
| Performance vs. Cost | Prefetch all subnodes | Better UX justifies additional LLM calls |
| Security vs. Usability | Optional OAuth | Easier development, production requires configuration |
| Flexibility vs. Complexity | Microservices | Independent scaling outweighs deployment complexity |

## 3.4 Quality Metrics

### 3.4.1 Current Metrics (via Langfuse)

| Metric | Description |
|--------|-------------|
| LLM latency | Time for LLM to generate response |
| Token count | Input/output tokens per request |
| Tool call frequency | How often paper_search is invoked |
| Error rate | Failed LLM or tool calls |

### 3.4.2 TODO: Metrics to Add

| Metric | Purpose |
|--------|---------|
| Time to first token | Measure streaming responsiveness |
| Prefetch hit rate | Effectiveness of prefetching |
| Session duration | User engagement |
| Questions per session | Usage patterns |

## 3.5 Quality Attribute Matrix

| Attribute | Priority | Achieved | Evidence |
|-----------|----------|----------|----------|
| Responsiveness | High | Yes | Streaming SSE + Socket.IO |
| Perceived Performance | High | Yes | Prefetching subnodes |
| Usability | High | Partial | Clean UI, but no user testing |
| Flexibility | Medium | Yes | Multiple LLM providers |
| Deployability | Medium | Yes | Pixi + Docker |
| Observability | Medium | Partial | Langfuse only, no app metrics |
| Security | Medium | Partial | OAuth works, defaults in code |
| Scalability | Low | Not addressed | Single-instance design |
| Reliability | Low | Not addressed | No HA, no persistent storage |

## 3.6 TODO: Quality Requirements Needing Input

The following quality requirements should be defined with stakeholders:

- [ ] **Availability**: What uptime is required? (e.g., 99.9%)
- [ ] **Scalability**: How many concurrent users must be supported?
- [ ] **Data Retention**: How long should chat history be kept?
- [ ] **Response Quality**: What accuracy level is acceptable for AI answers?
- [ ] **Accessibility**: Must the UI meet WCAG 2.1 AA standards?
