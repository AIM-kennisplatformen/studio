# Quality Attributes Section Template

**Purpose**: Document non-functional requirements that significantly influence architecture. These are the "ilities" that shape design decisions.

## Guidance

### What Quality Attributes Are
Quality attributes (also called non-functional requirements or cross-cutting concerns) describe HOW the system should behave, not WHAT it should do. They often drive the most significant architectural decisions.

### Prioritization Is Essential
- Identify the **top 3-5 quality attributes** that matter most for this system
- You cannot maximize everything - acknowledge trade-offs explicitly
- Document WHY certain qualities were prioritized (e.g., "We prioritize availability over consistency because...")

### Make Them Measurable
Quality attributes must be **specific and measurable** to be useful:
- ❌ Bad: "The system should be fast"
- ✅ Good: "95th percentile response time under 200ms for API calls"
- Include WHERE and HOW these are measured (dashboard links, test suites)

### Connect to Architecture
For each important quality attribute, briefly note how the architecture addresses it:
- "Scalability: Stateless services + horizontal pod autoscaling"
- "Security: JWT tokens + API gateway rate limiting"

### Common Quality Attributes to Consider
- **Performance**: Response time, throughput, latency
- **Scalability**: Handling growth in users, data, transactions
- **Availability**: Uptime, redundancy, failover
- **Security**: Authentication, authorization, encryption, audit
- **Fault Tolerance**: Graceful degradation, circuit breakers
- **Disaster Recovery**: Backup, restore, RTO/RPO
- **Accessibility**: WCAG compliance level
- **Internationalization**: Multi-language, multi-currency support
- **Auditability**: Logging, traceability, compliance
- **Maintainability**: Code quality, modularity, technical debt

### Anti-patterns to Avoid
- ❌ Don't list vague qualities without measurable targets
- ❌ Don't claim to optimize everything equally
- ❌ Don't ignore trade-offs between competing qualities
- ❌ Don't copy generic requirements - be specific to YOUR system

---

## Template

```markdown
# Quality Attributes

## Priority Quality Attributes

The following qualities are most critical for this system (in priority order):

1. **[Quality]** - [Why this matters most]
2. **[Quality]** - [Why this is important]
3. **[Quality]** - [Why this is important]

## Performance

| Metric | Target | Current | Measured At |
|--------|--------|---------|-------------|
| Response time (p95) | < 200ms | [measured] | [dashboard/tool] |
| Throughput | X req/s | [measured] | [dashboard/tool] |

**How architecture addresses this**: [brief explanation]

## Scalability

- Horizontal scaling approach: [description]
- Expected load: [metrics]
- Growth assumptions: [what we expect]

**How architecture addresses this**: [brief explanation]

## Security

- Authentication: [method]
- Authorization: [approach]
- Data encryption: [at-rest/in-transit]
- Audit logging: [what is logged]

**How architecture addresses this**: [brief explanation]

## Availability

- Target uptime: [percentage]
- Recovery time objective (RTO): [time]
- Recovery point objective (RPO): [time]
- Redundancy approach: [description]

**How architecture addresses this**: [brief explanation]

## Other Qualities

| Quality | Target | How Addressed |
|---------|--------|---------------|
| Accessibility | [WCAG level] | [approach] |
| Maintainability | [metrics] | [approach] |
| Testability | [coverage %] | [approach] |

## Trade-offs

| We Prioritize | Over | Because |
|---------------|------|---------|
| [Quality A] | [Quality B] | [Rationale] |
```

**Auto-discover from**: Test configs, CI thresholds, security configs, monitoring dashboards, SLA docs, performance tests
