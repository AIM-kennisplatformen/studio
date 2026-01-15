# Functional Overview Section Template

**Purpose**: Summarize WHAT the system does (not HOW). Help readers understand the functionality before diving into technical details.

## Guidance

### What This Section Should Accomplish
- Provide a high-level summary of major functions
- Help readers understand what makes this system useful
- Define key domain terminology
- Give a "feel" for the system through screenshots

### Level of Detail
- Summarize the **5-10 most important capabilities**, not every feature
- If formal requirements docs exist, reference them rather than duplicating
- Focus on what makes this system unique or interesting
- This is an overview, not a specification

### Organizing Functionality
- Group by **user goal** or **business capability**, not by technical module
- Use simple language a business stakeholder could understand
- Consider: "As a [user], I can [do what] to [achieve goal]"

### Screenshots
Include screenshots of important screens/pages to give readers a visual understanding:
- Capture the main dashboard or home screen
- Show key workflows (e.g., the checkout flow, the admin panel)
- Annotate screenshots if needed to highlight important elements
- Store images in a `/docs/images/` folder and reference them

### Domain Language
- Define key domain terms that appear throughout the codebase
- Use a glossary if the domain is complex
- Ensure terminology is consistent with what's used in code

### Anti-patterns to Avoid
- ❌ Don't duplicate detailed requirements documents
- ❌ Don't describe UI implementation details (colors, button placement)
- ❌ Don't include technical implementation details (that's the Architecture section)
- ❌ Don't list every minor feature or edge case

---

## Template

```markdown
# Functional Overview

## Core Capabilities

1. **[Capability Name]**
   - [Description]
   - Key workflows: [list]

2. **[Capability Name]**
   - [Description]
   - Key workflows: [list]

## Key Screens

[Include annotated screenshots of the most important screens/pages]

![Main Dashboard](./images/dashboard.png)
*The main dashboard showing [key elements]*

## Feature Summary

| Feature | Description | Status |
|---------|-------------|--------|
| [Name] | [What it does] | Active/Planned/Deprecated |

## User Journeys

### [Journey Name]
1. User does X
2. System responds with Y
3. User completes Z

## Domain Glossary

| Term | Definition |
|------|------------|
| [Domain term] | [What it means in this system's context] |
```

**Auto-discover from**: Route handlers, CLI commands, feature flags, test descriptions, API endpoints, UI components
