# External Interfaces Section Template

**Purpose**: Document how the system interfaces with the outside world. These are the integration points that other teams and systems depend on.

## Guidance

### What This Section Should Accomplish
- Define the contracts between your system and external parties
- Help consumers understand how to integrate with your system
- Help your team understand dependencies on external systems
- Document failure modes and fallback behaviors

### APIs You Provide

**What to document:**
- Base URL and versioning strategy (e.g., `/api/v1/`)
- Authentication method (API keys, OAuth, JWT)
- Link to detailed API documentation (OpenAPI/Swagger) - don't duplicate it here
- Rate limits and quotas
- SLAs if applicable (response time guarantees, uptime)

**Key point**: Document the contract, not implementation details. Consumers need to know what to expect, not how you built it.

### APIs You Consume

**What to document:**
- Why you depend on this service
- What happens when it's unavailable (fallback behavior, circuit breakers)
- Rate limits and quotas you must respect
- How credentials are managed (environment variables, secrets manager)
- Timeout and retry policies

**Key point**: External dependencies are risks. Document how you handle their failures.

### Asynchronous Interfaces (Events/Messages)

**What to document:**
- Message/event schemas (or link to schema registry)
- Ordering guarantees (FIFO, at-least-once, exactly-once)
- Idempotency requirements for consumers
- Dead letter queue handling
- Replay capabilities

### File-Based Interfaces

If your system exchanges files with other systems:
- File formats (CSV, JSON, XML, Parquet)
- Location and naming conventions
- Frequency of updates (real-time, hourly, daily)
- How failures are handled (retry, notification)

### Anti-patterns to Avoid
- ❌ Don't duplicate full API documentation - link to it
- ❌ Don't forget to document failure modes and fallbacks
- ❌ Don't skip authentication/authorization details
- ❌ Don't assume interfaces never change - note versioning strategy

---

## Template

```markdown
# External Interfaces

## APIs Provided

### [API Name]
- **Type**: REST / GraphQL / gRPC
- **Base URL**: [URL]
- **Versioning**: [strategy, e.g., URL path, header]
- **Authentication**: [method]
- **Rate Limits**: [limits if any]
- **Documentation**: [link to OpenAPI/Swagger]

## APIs Consumed

| Service | Purpose | Auth Method | Rate Limits | Failure Handling |
|---------|---------|-------------|-------------|------------------|
| [Name] | [Why used] | [How authenticated] | [Limits] | [Timeout/retry/fallback] |

### [Critical Dependency Name]

If a dependency is critical, document in more detail:
- **Purpose**: [why we need it]
- **Fallback behavior**: [what happens when unavailable]
- **Timeout policy**: [how long we wait]
- **Retry policy**: [how we retry]
- **Circuit breaker**: [if implemented]

## Events/Messages

### Published Events

| Event | Schema | Ordering | Consumers |
|-------|--------|----------|-----------|
| [Name] | [Link to schema] | [Guarantees] | [Who listens] |

### Consumed Events

| Event | Source | Handler | Idempotent? |
|-------|--------|---------|-------------|
| [Name] | [Producer] | [Code location] | [Yes/No - how] |

## File Interfaces

| Interface | Format | Location | Frequency | Direction |
|-----------|--------|----------|-----------|-----------|
| [Name] | [CSV/JSON/etc.] | [Path/S3 bucket] | [Schedule] | Import/Export |
```

**Auto-discover from**: OpenAPI specs, GraphQL schemas, message queue configs, webhook handlers, environment variables for external URLs
