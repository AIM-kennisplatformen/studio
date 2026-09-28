# Constraints Section Template

**Purpose**: Document things imposed upon you that limit design choices. Understanding constraints helps readers see WHY certain options weren't possible.

## Guidance

### Constraints vs. Principles
- **Constraints** are imposed upon you - you have no choice
- **Principles** are things you choose to follow
- If you could have done it differently but chose not to, that's a principle, not a constraint

### Categories of Constraints

**Time and Budget**
- Hard deadlines (e.g., regulatory compliance date, contract delivery)
- Resource limitations that affected scope or quality trade-offs

**Technology Constraints**
- Approved technology lists (corporate standards)
- Existing systems you must integrate with
- Platform requirements (must run on X, must support browser Y)

**People Constraints**
- Team size and availability
- Skill sets available (or not available)
- Geographic distribution, time zones

**Organizational Constraints**
- Corporate standards and policies
- Political factors ("the CTO wants us to use X")
- Legacy decisions you inherited

**Regulatory/Compliance Constraints**
- GDPR, HIPAA, PCI-DSS, SOC2
- Accessibility laws (ADA, WCAG requirements)
- Industry-specific regulations

### Document the Impact
For each constraint, explain how it affected architecture:
- "Must use Oracle DB (corporate standard) → influenced ORM choice, limited cloud provider options"
- "Team has no Go experience → chose Node.js despite performance trade-offs"

### Negotiable vs. Immovable
Some constraints can be challenged or negotiated:
- Mark which constraints are truly immovable vs. potentially flexible
- If a constraint was lifted, document that decision in the Decision Log

### Anti-patterns to Avoid
- ❌ Don't confuse constraints with design decisions you made freely
- ❌ Don't list constraints without explaining their impact on architecture
- ❌ Don't assume constraints are permanent - revisit periodically
- ❌ Don't hide constraints - transparency helps future teams understand decisions

---

## Template

```markdown
# Constraints

## Summary

Key constraints shaping this architecture:
1. [Most impactful constraint]
2. [Second most impactful]
3. [Third most impactful]

## Technology Constraints

| Constraint | Reason | Impact on Architecture | Negotiable? |
|------------|--------|------------------------|-------------|
| Must use [technology] | [why imposed] | [how it affects design] | Yes/No |
| Cannot use [technology] | [why prohibited] | [alternative chosen] | Yes/No |

## Organizational Constraints

| Constraint | Reason | Impact on Architecture |
|------------|--------|------------------------|
| Team size: [number] | [context] | [how it affected decisions] |
| Timeline: [deadline] | [why this date] | [what was descoped/rushed] |
| Budget: [amount/level] | [context] | [trade-offs made] |

## People Constraints

| Constraint | Impact |
|------------|--------|
| Team skills: [what's available] | [technologies chosen/avoided because of this] |
| Team location: [distribution] | [how this affected communication/architecture] |

## Regulatory/Compliance

| Regulation | Requirements | How Addressed |
|------------|--------------|---------------|
| [GDPR/HIPAA/etc.] | [specific requirements] | [architectural approach] |

## Third-Party Dependencies

| Dependency | Version Constraint | Reason | Risk |
|------------|-------------------|--------|------|
| [Library/Service] | [version/terms] | [why locked] | [what happens if unavailable] |
```

**Auto-discover from**: package.json engines, Dockerfile, .nvmrc, license files, compliance docs, corporate standards docs
