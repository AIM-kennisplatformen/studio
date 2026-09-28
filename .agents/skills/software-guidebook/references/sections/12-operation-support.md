# Operation & Support Section Template

**Purpose**: Document how to keep the software running in production. This is the operational knowledge needed during incidents and for day-to-day maintenance.

## Guidance

### What This Section Should Accomplish
- Enable on-call engineers to respond to incidents effectively
- Document tribal knowledge about system behavior
- Provide clear escalation paths
- Reduce mean time to resolution (MTTR)

### Monitoring Strategy

**What to monitor:**
- **Infrastructure metrics**: CPU, memory, disk, network
- **Application metrics**: Request rate, error rate, latency (RED method)
- **Business metrics**: Signups, transactions, conversions
- **Dependencies**: External service health, database connections

**Documentation should include:**
- What each metric means and why it matters
- Alert thresholds and why they were chosen
- Who gets alerted and how
- Dashboard locations and how to interpret them
- SLIs/SLOs if defined

### Logging

Document your logging strategy:
- **What's logged at each level**: When to use error, warn, info, debug
- **How to find logs**: Log aggregation tool, useful queries
- **Log retention**: How long logs are kept
- **Sensitive data**: What's redacted, what to never log
- **Correlation IDs**: How to trace requests across services

### Incident Response

**On-call:**
- Rotation schedule and how to swap
- Escalation paths and timeframes
- Contact methods (PagerDuty, phone, Slack)

**Incident severity levels:**
- Define what constitutes each severity
- Expected response times
- Who needs to be involved

**Communication:**
- Where to communicate during incidents (war room, Slack channel)
- Status page and how to update it
- Who communicates with customers

**Post-incident:**
- Blameless post-mortem process
- Where post-mortems are stored
- Follow-up action tracking

### Troubleshooting

Document common issues with:
- **Symptoms**: What alerts fire, what users report
- **Diagnosis**: How to confirm the issue, what to check
- **Resolution**: Step-by-step fix
- **Prevention**: How to prevent recurrence

Include:
- Diagnostic commands and tools
- Safe vs. dangerous operations (what NOT to do)
- When to escalate vs. handle yourself

### Maintenance Tasks

Document routine operational tasks:
- Scheduled maintenance windows
- Certificate renewals
- Database maintenance (vacuum, reindex, backups verification)
- Log rotation and cleanup
- Security patching schedule

### Anti-patterns to Avoid
- ❌ Don't assume operators know the system as well as developers
- ❌ Don't skip documenting "obvious" issues (they're not obvious at 3am)
- ❌ Don't forget escalation paths
- ❌ Don't leave runbooks outdated

---

## Template

```markdown
# Operation & Support

## Monitoring Overview

### Dashboards

| Dashboard | Purpose | Link |
|-----------|---------|------|
| [Main overview] | [System health at a glance] | [URL] |
| [Performance] | [Latency, throughput details] | [URL] |
| [Business metrics] | [Key business KPIs] | [URL] |

### Key Metrics

| Metric | What It Means | Normal Range | Alert Threshold |
|--------|---------------|--------------|-----------------|
| [Request rate] | [Requests per second] | [X-Y] | [< Z or > W] |
| [Error rate] | [5xx responses / total] | [< X%] | [> Y%] |
| [P95 latency] | [95th percentile response time] | [< X ms] | [> Y ms] |

### SLIs/SLOs (if defined)

| SLI | SLO Target | Current | Dashboard |
|-----|------------|---------|-----------|
| [Availability] | [99.9%] | [link to current] | [link] |
| [Latency] | [p99 < 500ms] | [link to current] | [link] |

## Alerting

### Alert Routing

| Alert | Severity | Notifies | Response Time |
|-------|----------|----------|---------------|
| [High error rate] | Critical | [On-call + team lead] | [15 min] |
| [Elevated latency] | Warning | [On-call] | [1 hour] |

### On-Call

- **Schedule**: [Link to rotation schedule]
- **Tool**: [PagerDuty/OpsGenie/etc.]
- **Escalation**: [Primary → Secondary → Team Lead → Manager]

## Logging

### Log Locations

| Log Type | Location | Retention |
|----------|----------|-----------|
| Application logs | [Datadog/CloudWatch/etc.] | [30 days] |
| Access logs | [Location] | [90 days] |
| Audit logs | [Location] | [1 year] |

### Useful Log Queries

```
# Find errors for a specific request
[query example]

# Trace a request across services
[query example]

# Find slow requests
[query example]
```

### Log Levels

| Level | When Used | Example |
|-------|-----------|---------|
| ERROR | Unexpected failures requiring attention | Failed database connection |
| WARN | Unusual but handled conditions | Retry succeeded after failure |
| INFO | Normal operational events | Request completed, job started |
| DEBUG | Detailed troubleshooting info | [When enabled] |

## Incident Response

### Severity Levels

| Severity | Definition | Response Time | Example |
|----------|------------|---------------|---------|
| Critical (P1) | Service down, data loss risk | Immediate | Complete outage |
| High (P2) | Major feature broken | 30 min | Payment processing failed |
| Medium (P3) | Degraded performance | 4 hours | Slow response times |
| Low (P4) | Minor issue | Next business day | Cosmetic bug |

### During an Incident

1. **Acknowledge** the alert in [tool]
2. **Assess** severity and impact
3. **Communicate** in [#incident-channel]
4. **Mitigate** using runbooks below
5. **Escalate** if needed: [escalation path]
6. **Resolve** and update status page
7. **Document** in post-incident review

### Communication

- **Internal channel**: [Slack #incidents]
- **Status page**: [URL and how to update]
- **Customer communication**: [Who handles, template location]

## Troubleshooting

### [Common Issue: High Error Rate]
- **Symptoms**: Error rate alert, user complaints
- **Diagnosis**:
  1. Check [dashboard] for error spike
  2. Run `[log query]` to identify error type
  3. Check recent deployments
- **Resolution**: [Steps to fix]
- **Escalate if**: [Conditions]

### [Common Issue: High Latency]
- **Symptoms**: Latency alert, slow page loads
- **Diagnosis**:
  1. Check [dashboard] for bottleneck
  2. Check database query times
  3. Check external service latency
- **Resolution**: [Steps to fix]
- **Escalate if**: [Conditions]

### [Common Issue: Database Connection Exhaustion]
- **Symptoms**: Connection timeout errors
- **Diagnosis**: [Steps]
- **Resolution**: [Steps]
- **Escalate if**: [Conditions]

### Diagnostic Commands

```bash
# Check service health
[command]

# View recent errors
[command]

# Check database connections
[command]
```

### ⚠️ Dangerous Operations

| Operation | Risk | Safe Alternative |
|-----------|------|------------------|
| [Direct database writes] | [Data corruption] | [Use admin tool] |
| [Restarting all instances] | [Full outage] | [Rolling restart] |

## Runbooks

| Runbook | When to Use | Link |
|---------|-------------|------|
| [Service restart] | [When service is unresponsive] | [Link] |
| [Database failover] | [Primary database down] | [Link] |
| [Scale up] | [High load] | [Link] |

## Maintenance Tasks

| Task | Frequency | Procedure | Last Run |
|------|-----------|-----------|----------|
| Certificate renewal | [Annual] | [Link or steps] | [Date] |
| Database maintenance | [Weekly] | [Link or steps] | [Date] |
| Security patching | [Monthly] | [Link or steps] | [Date] |

## Support Contacts

| Area | Primary Contact | Escalation |
|------|-----------------|------------|
| [Application] | [Team/Person] | [Manager] |
| [Infrastructure] | [Team/Person] | [Manager] |
| [Database] | [Team/Person] | [Manager] |
| [Security] | [Team/Person] | [Manager] |
```

**Auto-discover from**: Monitoring configs, logging setup, incident docs, runbooks, on-call schedules, post-mortems
