# Index Section Template

**Purpose**: The index provides orientation and navigation for the entire guidebook.

## Guidance

### What This Guidebook Is For
- **New joiners**: Get up to speed on the system's architecture and design
- **Existing team members**: Reference information when making changes
- **Everyone**: Understand the "big picture" that code alone cannot convey

This guidebook does NOT replace code-level documentation (comments, API docs). It captures the architectural context and rationale that would otherwise exist only in people's heads.

### Writing Style
- **Write for "the intelligent reader who isn't you"** - someone smart but unfamiliar with this codebase
- Avoid jargon without explanation; define domain terms on first use
- Balance technical depth with accessibility
- Use diagrams liberally - "a picture is worth a thousand words"

### Keep It Lightweight
Simon Brown warns against "overly long and detailed documents that nobody ever reads." Follow these guidelines:
- Each section should be **10-20 pages maximum**
- If a section grows too large, summarize and link to separate detailed docs
- Prefer bullet points and tables over prose where appropriate
- Include only information that helps readers understand the system

### Maintenance
- Treat this guidebook as code: if you change the architecture, update the guidebook
- Assign clear ownership for each section
- Review periodically (e.g., quarterly or after major releases)
- Mark sections with "Last reviewed: [DATE]" to track freshness

### How Different Readers Should Use This
| Reader | Start With | Focus On |
|--------|------------|----------|
| New developer | Context → Functional Overview → Code | Understanding what the system does and how to work in it |
| Architect/Tech Lead | Software Architecture → Principles → Decision Log | Design rationale and constraints |
| Operations/SRE | Infrastructure → Deployment → Operation & Support | How to run and maintain the system |

---

## Template

```markdown
# Software Guidebook: [Project Name]

> A living document describing the architecture and design of [Project Name].
> Last updated: [DATE]

## About This Guidebook

This guidebook follows Simon Brown's Software Guidebook format from
"Software Architecture for Developers Vol. 2". It serves as the primary
architecture documentation for onboarding new team members and preserving
architectural knowledge.

> **Writing Guidelines**
> - Target audience: An intelligent reader who isn't you
> - Keep sections concise (10-20 pages max each)
> - Summarize, don't duplicate - link to detailed docs where needed
> - Update when architecture changes - treat as code

## Sections

1. [Context](01-context.md) - What is this system and who uses it?
2. [Functional Overview](02-functional-overview.md) - What does it do?
3. [Quality Attributes](03-quality-attributes.md) - Non-functional requirements
4. [Constraints](04-constraints.md) - Limitations and boundaries
5. [Principles](05-principles.md) - Guiding design decisions
6. [Software Architecture](06-software-architecture.md) - C4 diagrams and structure
7. [External Interfaces](07-external-interfaces.md) - APIs and integrations
8. [Code](08-code.md) - Code organization and patterns
9. [Data](09-data.md) - Data models and storage
10. [Infrastructure](10-infrastructure.md) - Deployment environments
11. [Deployment](11-deployment.md) - How to deploy
12. [Operation & Support](12-operation-support.md) - Running in production
13. [Decision Log](13-decision-log.md) - Architecture decisions

## Quick Links

- [Getting Started](../README.md)
- [API Documentation](../api/)
- [Contributing Guide](../CONTRIBUTING.md)
```
