# 2. Functional Overview

This chapter provides an overview of the key features and capabilities of the Studio application.

## 2.1 Core Features

The Studio application provides an interactive knowledge exploration platform with AI-powered question answering.

![Studio Features Mindmap](02-features-mindmap.png)

<details>
<summary>Mermaid source</summary>

```mermaid
mindmap
  root((Studio Features))
    Knowledge Graph
      Interactive visualization
      Node navigation
      Relationship exploration
    AI Chat
      Natural language Q&A
      Evidence-based answers
      Streaming responses
    Literature Search
      Zotero integration
      Semantic search
      Citation support
    Authentication
      OAuth/OIDC
      Session management
```

</details>

## 2.2 Feature Details

### 2.2.1 Interactive Knowledge Graph

The application displays a knowledge graph that users can explore visually.

**Capabilities**:
- View domain concepts as nodes
- See relationships between concepts as edges
- Click nodes to navigate and get context
- Resizable split-panel layout

**Implementation**:
- React Flow for graph rendering ([`src/frontend/src/graph.jsx`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/frontend/src/graph.jsx))
- Graph data loaded from JSON ([`example-data.json`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/frontend/src/knowledge-graph/example-data.json))

**Current Graph Structure** (Energy Poverty domain):

![Knowledge Graph Structure](02-knowledge-graph.png)

<details>
<summary>Mermaid source</summary>

```mermaid
flowchart TB
    1[Energy Poverty: Intervention strategies]
    2[Best practices]
    3[Target groups]
    4[Strategic overview]
    5[Scientific literature]
    6[Grey literature]
    7[Project reports]

    1 --> 2
    1 --> 3
    1 --> 4
    2 --> 5
    2 --> 6
    2 --> 7
```

</details>

### 2.2.2 AI-Powered Chat

Users can ask natural language questions and receive evidence-informed answers.

**Capabilities**:
- Type questions in natural language
- Receive streaming responses in real-time
- See "thinking" indicator while processing
- Responses cite relevant literature

**User Flow**:

![Chat Sequence Diagram](02-chat-sequence.png)

<details>
<summary>Mermaid source</summary>

```mermaid
sequenceDiagram
    participant User
    participant Chat UI
    participant Backend
    participant LLM

    User->>Chat UI: Type question
    User->>Chat UI: Press send
    Chat UI->>Backend: WebSocket message
    Chat UI->>User: Show "Thinking..."
    Backend->>LLM: Process with tools
    loop Streaming
        LLM-->>Backend: Token
        Backend-->>Chat UI: Message event
        Chat UI-->>User: Update response
    end
    Backend-->>Chat UI: Done event
    Chat UI-->>User: Final response
```

</details>

### 2.2.3 Literature-Backed Responses

The AI assistant searches academic literature to support its answers.

**Capabilities**:
- Automatic literature search via MCP tool
- Semantic matching using vector embeddings
- Bibliography metadata from Zotero
- Relevance scores for citations

**How It Works**:

1. User asks a question
2. LLM invokes `paper_search` tool with question + keywords
3. MCP server queries Zotero for papers matching keywords
4. Qdrant performs semantic search on paper content
5. Results returned to LLM for synthesis
6. LLM generates answer citing relevant sources

### 2.2.4 Prefetched Subnode Answers

When a user asks a question at the root node, the system prefetches answers for subnodes in the background.

**Subnodes**:
- Best practices
- Target groups
- Strategic overview

**Benefits**:
- Instant responses when navigating to subnodes
- Improved perceived performance
- Better user experience

### 2.2.5 User Authentication

Optional OAuth authentication via Authentik.

**Capabilities**:
- Login via external identity provider
- Session-based authentication
- Automatic redirect for protected resources
- Logout functionality

## 2.3 User Journeys

### 2.3.1 First-Time User

![First-Time User Journey](02-first-time-user-journey.png)

<details>
<summary>Mermaid source</summary>

```mermaid
journey
    title First-Time User Journey
    section Login
      Navigate to app: 3: User
      Redirect to Authentik: 5: System
      Enter credentials: 3: User
      Redirect back: 5: System
    section Explore
      View knowledge graph: 5: User
      Read node labels: 4: User
      Click on nodes: 5: User
    section Ask Questions
      Type first question: 5: User
      Wait for response: 3: User
      Read AI answer: 5: User
      Navigate to subnode: 5: User
      See instant answer: 5: User
```

</details>

### 2.3.2 Research Session

![Research Session Journey](02-research-session-journey.png)

<details>
<summary>Mermaid source</summary>

```mermaid
journey
    title Research Session
    section Question Root Topic
      Ask about intervention strategies: 5: User
      Read evidence-based answer: 5: User
      Note cited sources: 4: User
    section Explore Subtopics
      Click "Best practices": 5: User
      See prefetched answer: 5: User
      Click "Target groups": 5: User
      See prefetched answer: 5: User
    section Deep Dive
      Ask follow-up question: 5: User
      Wait for new search: 3: User
      Read detailed response: 5: User
```

</details>

## 2.4 Feature Matrix

| Feature | Status | Implementation |
|---------|--------|----------------|
| Knowledge graph visualization | Complete | React Flow |
| Node click navigation | Complete | Graph endpoint |
| AI chat interface | Complete | Socket.IO + LLM Worker |
| Streaming responses | Complete | SSE + WebSocket |
| Literature search | Complete | Zotero + Qdrant |
| Subnode prefetching | Complete | Async tasks |
| OAuth authentication | Complete | Authentik |
| Chat history persistence | Not implemented | In-memory only |
| Multi-user rooms | Not implemented | Single user per session |
| Graph editing | Not implemented | Read-only |

## 2.5 Domain Context

The current deployment focuses on **Energy Poverty** research:

| Concept | Description |
|---------|-------------|
| Energy Poverty | Inability to afford adequate energy services |
| Intervention Strategies | Approaches to address energy poverty |
| Best Practices | Proven effective methods |
| Target Groups | Populations most affected |
| Strategic Overview | Policy and planning perspectives |

The system is domain-agnostic; replacing the knowledge graph JSON and Qdrant collection would adapt it to other domains.

## 2.6 Limitations

1. **Read-only graph**: Users cannot modify the knowledge graph through the UI
2. **No persistent history**: Chat sessions are lost on server restart
3. **Single collection**: Only one Qdrant collection is supported
4. **Fixed subnodes**: Prefetch targets are hardcoded to three specific nodes
5. **No multi-turn context**: Each question is processed independently (no conversation memory passed to LLM)
