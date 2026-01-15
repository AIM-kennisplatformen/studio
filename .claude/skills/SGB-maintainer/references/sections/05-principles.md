# Principles Section Template

**Purpose**: Document the guiding rules your team has CHOSEN to follow. Principles introduce consistency and help teams make autonomous decisions.

## Guidance

### What Principles Are
- Principles are **choices** you make to introduce consistency and clarity
- They differ from constraints (imposed) - principles are things you WANT to follow
- They provide a framework for making consistent decisions without constant escalation
- They answer: "When faced with a choice, what do we prefer?"

### Characteristics of Good Principles
- **Concise and memorable**: If people can't remember them, they won't use them
- **Specific to your context**: Not generic motherhood statements
- **Actionable**: Clear implications for what you WILL and WON'T do
- **Limited in number**: 5-10 principles is usually enough; too many = none

### Principle Structure
Each principle should include:
1. **Statement**: The principle itself (short, memorable)
2. **Rationale**: Why this matters for THIS system specifically
3. **Implications**: What you WILL do and WON'T do because of this
4. **Examples**: Concrete decisions guided by this principle

### Common Principle Categories

**Technology Selection**
- "Prefer proven technologies over cutting-edge"
- "Prefer buying/using over building"
- "Prefer open source with active communities"

**Architecture & Design**
- "Favor simplicity over cleverness"
- "Design for failure"
- "Keep services stateless where possible"

**Data Management**
- "Single source of truth for each data entity"
- "Data belongs to services, not shared databases"

**Integration**
- "Prefer asynchronous communication between services"
- "APIs must be versioned"

**Security**
- "Secure by default"
- "Principle of least privilege"

### Anti-patterns to Avoid
- ❌ Don't list generic principles that apply to any system ("write clean code")
- ❌ Don't create principles without concrete implications
- ❌ Don't have so many principles that nobody remembers them
- ❌ Don't confuse principles with constraints (principles are choices)

---

## Template

```markdown
# Principles

## Overview

These principles guide our architectural and design decisions. When facing a choice, refer to these to maintain consistency.

## Architecture Principles

### [Principle Name]
- **Statement**: [concise, memorable principle]
- **Rationale**: [why this matters for THIS system]
- **Implications**:
  - We WILL: [concrete behavior]
  - We WON'T: [what we avoid]
- **Example**: [a decision guided by this principle]

### [Principle Name]
- **Statement**: [concise, memorable principle]
- **Rationale**: [why this matters for THIS system]
- **Implications**:
  - We WILL: [concrete behavior]
  - We WON'T: [what we avoid]
- **Example**: [a decision guided by this principle]

## Design Principles

| Principle | Implication |
|-----------|-------------|
| [Principle] | [What this means in practice] |
| [Principle] | [What this means in practice] |

## Coding Standards

| Area | Standard | Enforced By |
|------|----------|-------------|
| Formatting | [style guide or description] | [ESLint/Prettier/etc.] |
| Naming | [conventions] | [code review/linter] |
| Error handling | [approach] | [code review] |

## Principles Summary

Quick reference (for memorability):
1. [Principle 1 - one line]
2. [Principle 2 - one line]
3. [Principle 3 - one line]
4. [Principle 4 - one line]
5. [Principle 5 - one line]
```

**Auto-discover from**: ARCHITECTURE.md, CONTRIBUTING.md, .eslintrc, .prettierrc, ADRs, code review comments
