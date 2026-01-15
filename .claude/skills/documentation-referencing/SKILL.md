---
name: documentation-referencing
description: Add comprehensive cross-references and hyperlinks throughout generated documentation. Use this skill when writing documentation that needs to link to source code (GitHub), other documentation sections, PDF/Word documents with page references, or when creating Mermaid diagrams with clickable nodes. Triggers on requests to "add references", "link to source", "cross-reference documentation", "create linked documentation", or any documentation task requiring rich interconnection between code, docs, and supporting materials.
---

# Documentation Referencing

Create richly interconnected documentation allowing readers to navigate seamlessly between concepts, source code, and supporting documents.

## Core Principle

Every significant concept, component, function, class, or configuration MUST link to:
1. Its implementation in source code
2. Related sections in the documentation
3. Supporting documents (specs, designs, external references)

## Reference Density

- 3-5 hyperlinks per major section minimum
- Each code concept links to its source
- Each architectural term links to its definition
- Cross-link bidirectionally: if A mentions B, B should mention A

## Link Formats

### Source Code (GitHub)

```
Single line:   https://github.com/{org}/{repo}/blob/{branch}/{path}#L{line}
Line range:    https://github.com/{org}/{repo}/blob/{branch}/{path}#L{start}-L{end}
Whole file:    https://github.com/{org}/{repo}/blob/{branch}/{path}
```

Examples:
```markdown
The [`authenticateUser()`](https://github.com/org/repo/blob/main/src/auth/login.ts#L45-L78) function handles OAuth2 token validation.

Request flow: [`validateInput()`](https://github.com/org/repo/blob/main/src/api/validators.ts#L23-L45) → [`processRequest()`](https://github.com/org/repo/blob/main/src/api/handlers.ts#L67-L102) → [`formatResponse()`](https://github.com/org/repo/blob/main/src/api/formatters.ts#L15-L38).
```

### Documentation Cross-References

```
Same file:       [Link Text](#header-anchor-id)
Same directory:  [Link Text](other-file.md#header-anchor-id)
Different dir:   [Link Text](../path/to/file.md#header-anchor-id)
```

Anchor generation: lowercase, spaces→hyphens, special chars removed.
- `## System Architecture` → `#system-architecture`
- `### 1. Authentication Flow` → `#1-authentication-flow`
- `## API Endpoints & Routes` → `#api-endpoints--routes`

### PDF and Word Documents

Include page numbers in link TEXT (not URL):
```markdown
[Technical Specification (p. 24)](../specs/technical-spec.pdf)
[Database Design (pp. 12-18)](../design/database-design.docx)
[Security Guidelines (Section 4.2, pp. 31-35)](../compliance/security-guidelines.pdf)
```

## Mermaid Diagrams with Clickable Nodes

Different diagram types use different syntax for interactivity:

### Flowcharts

Use `click NodeId "URL" "tooltip"` after node/edge definitions:

```mermaid
flowchart TD
    A[Client Request] --> B[API Gateway]
    B --> C[Auth Service]
    C --> D{Valid Token?}
    D -->|Yes| E[Business Logic]
    D -->|No| F[401 Unauthorized]

    click A "#client-architecture" "View client architecture"
    click B "https://github.com/org/repo/blob/main/src/gateway/index.ts#L1-L50" "View API Gateway source"
    click C "https://github.com/org/repo/blob/main/src/auth/service.ts#L20-L85" "View Auth Service"
    click E "./business-logic.md#overview" "View business logic docs"
```

### Sequence Diagrams

Use `link ParticipantId: Label @ URL` syntax:
```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant D as Database

    C->>A: POST /users
    A->>D: INSERT user
    D-->>A: user_id
    A-->>C: 201 Created

    link C: Client SDK @ #client-sdk
    link A: Source @ https://github.com/org/repo/blob/main/src/api/users.ts#L45-L78
    link D: Schema @ ./data-layer.md#user-table-schema
```

### Class Diagrams

Use `click ClassName href "URL" "tooltip"` (requires `href` keyword):
```mermaid
classDiagram
    class UserService {
        +createUser()
        +findById()
    }
    class UserRepository {
        +save()
        +findOne()
    }
    UserService --> UserRepository

    click UserService href "https://github.com/org/repo/blob/main/src/services/user.service.ts#L1-L85" "View UserService"
    click UserRepository href "https://github.com/org/repo/blob/main/src/repositories/user.repository.ts#L1-L62" "View UserRepository"
```

### C4 Diagrams (Context, Container, Component)

Use the `$link` parameter at the end of element definitions:

```
Person(alias, "Label", "Description", $link="URL")
System(alias, "Label", "Description", $link="URL")
Container(alias, "Label", "Technology", "Description", $link="URL")
Component(alias, "Label", "Technology", "Description", $link="URL")
```

Context diagram example:
```mermaid
C4Context
    title System Context with Links

    Person(user, "User", "Application user", $link="#user-personas")
    System(app, "Application", "Main system", $link="https://github.com/org/repo/blob/main/src/app")
    System_Ext(payment, "Payment API", "Processes payments", $link="https://docs.stripe.com")

    Rel(user, app, "Uses")
    Rel(app, payment, "Charges cards", "HTTPS")
```

Container diagram example:
```mermaid
C4Container
    title Container Diagram with Links

    System_Boundary(app, "Application") {
        Container(web, "Web App", "Next.js", "Serves UI", $link="https://github.com/org/repo/blob/main/src/web")
        Container(api, "API", "Node.js", "Business logic", $link="https://github.com/org/repo/blob/main/src/api")
        ContainerDb(db, "Database", "PostgreSQL", "Stores data", $link="./09-data.md#schema")
    }

    Rel(web, api, "Calls", "HTTPS")
    Rel(api, db, "Reads/writes", "SQL")
```

Component diagram example:
```mermaid
C4Component
    title Component Diagram with Links

    Container_Boundary(api, "API Server") {
        Component(auth, "Auth Controller", "Express", "Authentication", $link="https://github.com/org/repo/blob/main/src/api/auth.ts#L1-L50")
        Component(users, "User Service", "TypeScript", "User logic", $link="https://github.com/org/repo/blob/main/src/services/user.ts#L1-L120")
    }

    Rel(auth, users, "Uses")
```

## Tables with Links

| Component | Description | Source | Documentation |
|-----------|-------------|--------|---------------|
| [`AuthService`](https://github.com/org/repo/blob/main/src/auth/service.ts#L15-L120) | Authentication | [auth/service.ts](https://github.com/org/repo/blob/main/src/auth/service.ts) | [Authentication](#authentication) |
| [`DataProcessor`](https://github.com/org/repo/blob/main/src/core/processor.ts#L1-L200) | Data transformation | [core/processor.ts](https://github.com/org/repo/blob/main/src/core/processor.ts) | [Data Processing](./data-processing.md) |

## Citation Blocks

End each major section with a Sources block:

```markdown
**Sources:**
- [`src/auth/service.ts:L15-L85`](https://github.com/org/repo/blob/main/src/auth/service.ts#L15-L85) - Authentication service
- [`config/auth.yml`](https://github.com/org/repo/blob/main/config/auth.yml) - Auth configuration
- [Security Guidelines (pp. 31-35)](../compliance/security-guidelines.pdf) - Compliance requirements
- [API Security](#api-security) - Related documentation section
```

## Best Practices

- Use descriptive link text; avoid "click here"
- Prefer specific line ranges over whole-file links
- Use branch references (main/develop) rather than commit SHAs
- Add tooltips to Mermaid click statements
- Group related links at section ends
- Use consistent URL patterns throughout
