# Context Section Template

**Purpose**: Set the scene. Answer "What is this thing and what role does it play?"

## Guidance

### What This Section Should Accomplish
- Define the system's scope and boundaries (what's IN vs OUT)
- Explain WHY this system exists (business drivers, problems solved)
- Show how the system fits into the broader landscape
- Be understandable by non-technical stakeholders

### Writing the System Overview
Answer these questions in 1-2 paragraphs:
- What is this system?
- What problem does it solve?
- Who is it for?
- What value does it provide?

### Creating the Context Diagram (C4 Level 1)
- Show your system as a **single box** in the center
- Surround it with users (stick figures) and external systems (boxes)
- Draw lines showing relationships with brief labels (e.g., "sends orders to")
- Include direction of data/interaction flow
- **Keep it simple**: A non-technical stakeholder should understand it

### Anti-patterns to Avoid
- ❌ Don't show internal components (save for Container diagram)
- ❌ Don't list every API endpoint (save for External Interfaces)
- ❌ Don't include systems with no direct interaction
- ❌ Don't use technical jargon in labels

### Stakeholders vs Users
- **Users**: People who directly interact with the system
- **Stakeholders**: Anyone who cares about the system (business owners, compliance, downstream teams, ops)

---

## Template

```markdown
# Context

## System Overview

[One paragraph describing what this system is and its primary purpose]

## Why This System Exists

- **Business drivers**: [What business need prompted this system?]
- **Problems solved**: [What pain points does it address?]
- **Value provided**: [What benefits does it deliver?]

## System Context Diagram

[C4 Context Diagram - your system as a single box, surrounded by users and external systems]

## Users and Personas

| User Type | Description | How They Use the System |
|-----------|-------------|------------------------|
| [Role] | [Who they are] | [What they do] |

## Stakeholders

| Stakeholder | Concern |
|-------------|---------|
| [Person, Organization or Group] | [Interest or problem with the system] |

## External Systems

| System | Direction | Purpose |
|--------|-----------|---------|
| [Name] | Inbound/Outbound/Both | [What data/functionality] |

## Scope Boundaries

- **In scope**: [What this system IS responsible for]
- **Out of scope**: [What this system is NOT responsible for]
```

**Auto-discover from**: README.md, docs/, OAuth configs, API client configs, external service URLs in env files
