# Decision Log Section Template

**Purpose**: Capture significant architectural decisions with their context and rationale. This preserves institutional knowledge that would otherwise be lost when team members leave.

## Guidance

### Why Record Decisions?
- Decisions are often made in meetings or Slack threads, then forgotten
- New team members ask "why did we do it this way?" with no answer
- Understanding past constraints prevents repeating mistakes
- Helps future teams understand WHY, not just WHAT

### What to Record

**Record architecturally significant decisions:**
- Technology choices (database, framework, language)
- Structural decisions (monolith vs. microservices, module boundaries)
- Integration approaches (sync vs. async, API design)
- Decisions that were contentious or surprising
- Decisions that constrain future options
- Decisions to NOT do something (often as valuable as what you chose)

**Don't record:**
- Every small implementation choice
- Decisions that are easily reversible
- Standard practices that need no justification

### When to Write ADRs

- **Write immediately**: Capture decisions when made, not months later
- **Include rejected alternatives**: Document what you considered and why you didn't choose it
- **Update, don't delete**: When decisions change, mark old ADRs as superseded
- **Avoid revisionist history**: Record what you actually knew at the time

### ADR Lifecycle

| Status | Meaning |
|--------|---------|
| Proposed | Under discussion, not yet decided |
| Accepted | Decision made and in effect |
| Deprecated | No longer relevant (system changed) |
| Superseded | Replaced by a newer decision (link to it) |

### Making ADRs Discoverable

- Use clear, searchable titles
- Add tags/categories for filtering
- Keep the decision index updated
- Link related ADRs together

### Anti-patterns to Avoid
- ❌ Don't write ADRs after the fact with revisionist history
- ❌ Don't skip recording rejected alternatives - they're valuable context
- ❌ Don't let ADRs become outdated without marking them superseded
- ❌ Don't make ADRs too long - be concise, link to details if needed
- ❌ Don't forget to update the index when adding new ADRs

---

## Template

````markdown
# Decision Log

Track significant architecture decisions using ADR format. These records preserve the context and rationale behind decisions that shape the system.

## How to Use This Log

1. When making a significant decision, create a new ADR
2. Discuss in PR/review before marking as Accepted
3. Update the index below
4. When superseding a decision, update the old ADR's status

## Decisions Index

| ID | Title | Status | Date | Tags |
|----|-------|--------|------|------|
| ADR-001 | [Title] | Accepted | [Date] | [technology, database] |
| ADR-002 | [Title] | Accepted | [Date] | [architecture] |
| ADR-003 | [Title] | Superseded by ADR-005 | [Date] | [integration] |

---

## ADR-001: [Descriptive Title]

### Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

### Date
[YYYY-MM-DD]

### Decision Drivers
- [Driver 1: What constraint or goal influenced this decision?]
- [Driver 2: What quality attribute mattered?]
- [Driver 3: What constraint limited options?]

### Context
[What is the situation? What problem are we solving? What forces are at play?]

### Options Considered

**Option 1: [Name]**
- Pros: [advantages]
- Cons: [disadvantages]

**Option 2: [Name]**
- Pros: [advantages]
- Cons: [disadvantages]

**Option 3: [Name]**
- Pros: [advantages]
- Cons: [disadvantages]

### Decision
[What is the decision? Be specific about what we will do.]

### Consequences

**Positive:**
- [What becomes easier?]
- [What problems does this solve?]

**Negative:**
- [What becomes harder?]
- [What new problems might arise?]
- [What options are we closing off?]

**Neutral:**
- [What trade-offs are we accepting?]

### Related Decisions
- [ADR-XXX: Related decision]
- [ADR-YYY: Decision this builds on]
````

## ADR Template (Minimal)

For simpler decisions, use this shorter format:

```markdown
## ADR-XXX: [Title]

**Status**: [Accepted] | **Date**: [YYYY-MM-DD]

**Context**: [1-2 sentences on the problem]

**Decision**: [What we decided]

**Consequences**: [Key trade-offs, 2-3 bullets]
```

**Auto-discover from**: docs/adr/, docs/decisions/, existing ADRs, PR discussions, meeting notes
