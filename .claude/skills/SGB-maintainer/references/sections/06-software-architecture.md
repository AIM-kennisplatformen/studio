# Software Architecture Section Template

**Purpose**: Show the structure of the system using C4 model diagrams. This is the heart of technical documentation.

## Guidance

### The C4 Model Overview
The C4 model provides four levels of abstraction:
1. **System Context** (Level 1) - covered in the Context section
2. **Container Diagram** (Level 2) - high-level technology choices
3. **Component Diagram** (Level 3) - logical components within containers
4. **Code** (Level 4, optional) - class diagrams, covered in Code section

### Container Diagram (Level 2)

**What is a container?**
A container is something that needs to be running for the system to work. Containers are typically **separately deployable processes** (or groups of processes in distributed systems like message queues or databases).

Examples of containers:
- Web application (React SPA, Angular app)
- API server (Node.js Express, Python FastAPI)
- Database (PostgreSQL, MongoDB)
- Message queue (RabbitMQ, Kafka)
- File storage (S3, local filesystem)
- Background worker (Celery worker, cron jobs)

**What to show on a container diagram:**
- Each container as a box with name AND technology (e.g., "API Server [Node.js/Express]")
- Communication between containers with protocols (HTTP/REST, WebSocket, SQL, AMQP)
- External systems the containers interact with
- Users/personas that interact with each container

**Key point**: The container diagram shows your key technology decisions at a glance.

### Component Diagram (Level 3)

**Important**: Components here are NOT "components" in the React, Angular, or any other framework sense. A C4 component is a **major structural building block** within a container - a logical grouping of related functionality with a well-defined interface.

**Good component candidates:**
- Controllers and API handlers
- Business logic services
- Data access layers / Repositories
- Integration adapters (e.g., payment gateway adapter)
- Core domain models / aggregates
- Authentication/authorization modules
- Event handlers / message processors

**Avoid showing:**
- Utility classes and helpers
- Simple data transfer objects (DTOs)
- Configuration classes
- Minor implementation details
- Every class, method, or property

**Decision criteria for including a component:**
Ask these questions:
1. Does it have a well-defined interface? → If yes, include
2. Is it a logical grouping of related functionality? → If yes, include
3. Does showing it aid architectural understanding? → If yes, include
4. Would a developer discuss it as a distinct "thing"? → If yes, include
5. Is it just an implementation detail? → If yes, exclude

**When to create component diagrams:**
- Only for containers that warrant deeper explanation
- Focus on complex or critical containers
- Skip simple containers (e.g., a static file server doesn't need one)

### Diagram Notation Guidelines
- Use simple boxes and lines
- Label relationships with verbs and protocols ("reads from [SQL]", "sends events to [AMQP]")
- Include a key/legend if using colors or special notation
- Keep diagrams simple enough to fit on one page
- Use consistent shapes: boxes for containers/components, cylinders for databases, stick figures for users

### Anti-patterns to Avoid
- ❌ Don't create diagrams too detailed to understand at a glance
- ❌ Don't skip technologies on container diagrams - they're the point
- ❌ Don't mix abstraction levels in one diagram
- ❌ Don't show every class as a component
- ❌ Don't create component diagrams for simple containers

---

## Template

```markdown
# Software Architecture

## Container Diagram

[Mermaid C4 Container diagram showing all containers and their interactions]

### Containers

| Container | Kind | Technology | Purpose | Communicates With |
|-----------|------|------------|---------|-------------------|
| [Name] | [Process, Machine, Docker, Distributed system etc.] | [Tech stack] | [What it does] | [Other containers, protocols] |

## Component Diagram: [Container Name]

[Only create for containers that need deeper explanation]

[Mermaid C4 Component diagram]

### Components

| Component | Kind | Responsibility | Key Interfaces |
|-----------|------|---------------|----------------|
| [Name] | [function, class, file, module, app (or framework concepts)] | [What it does] | [APIs/methods it exposes] |

## Component Diagram: [Another Container Name]

[Repeat as needed for complex containers]

## Key Architectural Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| [Technology/pattern choice] | [Brief why] | [Link to ADR if exists] |
```

**Auto-discover from**: src/ directory structure, package.json workspaces, imports/exports, service boundaries, Docker/k8s configs
