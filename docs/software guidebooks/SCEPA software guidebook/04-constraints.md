# 4. Constraints

This chapter documents external constraints that the development team cannot change or influence. These are imposed by organizational, regulatory, or external factors.

## 4.1 Overview

Constraints differ from technical decisions in that they are **non-negotiable** requirements imposed from outside the team. The team must work within these boundaries rather than choosing them.

> **Note**: This section documents constraints that could be inferred from the codebase. Actual organizational constraints may exist that are not visible in the code. Teams should supplement this section with their specific constraints.

## 4.2 Identified Constraints

Based on the codebase analysis, the following potential constraints have been identified:

### 4.2.1 Python Version Requirement

**Constraint**: Python 3.11 or higher required

**Source**: [`pyproject.toml:28`](https://github.com/AIM-kennisplatformen/studio/blob/main/pyproject.toml#L28)

```toml
requires-python = ">=3.11"
```

**Rationale**: Likely driven by dependency requirements (FastAPI, LangChain) or organizational Python version policy.

**Impact**: Development and deployment environments must support Python 3.11+.

### 4.2.2 Authentik as Identity Provider

**Constraint**: OAuth authentication must use Authentik

**Source**: [`src/backend/endpoints/auth.py:12-18`](https://github.com/AIM-kennisplatformen/studio/blob/main/src/backend/endpoints/auth.py#L12-L18)

**Rationale**: Organization may have standardized on Authentik for identity management.

**Impact**: Cannot use alternative identity providers without code changes.

## 4.3 Potential Constraints (Require Confirmation)

The following may be constraints but require confirmation from stakeholders:

### 4.3.1 Zotero for Bibliography

**Possible Constraint**: Use Zotero for reference management

**Evidence**: Deep integration with Zotero API for paper metadata

**Questions for Stakeholders**:
- Is Zotero mandated by the organization?
- Are alternative bibliography systems acceptable?

### 4.3.2 Self-Hosted Deployment

**Possible Constraint**: Application must be self-hostable

**Evidence**: Docker Compose setup, Pixi for reproducible environments, support for local Ollama

**Questions for Stakeholders**:
- Are cloud-only deployments acceptable?
- Is there a requirement for air-gapped deployment?

## 4.4 What Is NOT a Constraint

The following are technical decisions made by the team, not external constraints:

| Decision | Why It's Not a Constraint |
|----------|---------------------------|
| FastAPI | Team choice for Python web framework |
| React | Team choice for frontend framework |
| Qdrant | Team choice for vector database |
| Jotai | Team choice for state management |
| Docker | Team choice for containerization |
| Pixi | Team choice for package management |

These decisions are documented in [Chapter 13: Decision Log](13-decision-log.md).

## 4.5 Template for Documenting Constraints

When new constraints are identified, document them using this template:

```markdown
### X.X.X Constraint Name

**Constraint**: Brief description of what must or must not be done

**Source**: Where does this constraint come from?
- Regulatory requirement (cite regulation)
- Organizational policy (cite policy document)
- External system requirement
- Contractual obligation

**Rationale**: Why does this constraint exist?

**Impact**: How does this affect the system design or development?

**Expiration**: Does this constraint have an end date?
```

## 4.6 TODO: Constraints Requiring Stakeholder Input

The following constraints are typically relevant but not discoverable from code:

- [ ] **Budget Constraints**: Are there cost limits for cloud services or LLM API usage?
- [ ] **Timeline Constraints**: Are there fixed delivery dates?
- [ ] **Regulatory Compliance**: Are there data protection requirements (GDPR, etc.)?
- [ ] **Accessibility Requirements**: Must the application meet WCAG standards?
- [ ] **Browser Support**: Which browsers must be supported?
- [ ] **Data Residency**: Must data be stored in specific geographic regions?
- [ ] **Audit Requirements**: Are there logging or audit trail requirements?
