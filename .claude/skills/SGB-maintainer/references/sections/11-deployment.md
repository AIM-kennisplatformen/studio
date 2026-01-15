# Deployment Section Template

**Purpose**: Document how software gets from development to production. Enable anyone to understand and execute deployments safely.

## Guidance

### What This Section Should Accomplish
- Enable any team member to deploy (reduce bus factor)
- Document the full path from commit to production
- Provide clear rollback procedures for incidents
- Explain verification steps to confirm success

### Deployment Philosophy

Document your approach:
- **Frequency**: How often do you deploy? (continuous, daily, weekly, on-demand)
- **Strategy**: Blue-green, canary, rolling updates, or all-at-once?
- **Feature flags**: Do you use them to decouple deployment from release?
- **Dark launches**: Can features be deployed but hidden?

### CI/CD Pipeline

Document each stage clearly:
- What triggers the pipeline (push, PR merge, manual)
- What each stage does and how long it typically takes
- Approval gates and who can approve
- Where to find logs and status
- What causes failures and how to fix common issues

### Deployment Prerequisites

What must be in place before deploying:
- Required permissions and access (who can deploy)
- Environment preparation steps
- Database migrations (when to run, order, rollback plan)
- Dependency updates
- Configuration changes

### Verification and Monitoring

How to confirm deployment succeeded:
- Automated smoke tests
- Health check endpoints
- Key metrics to watch
- How long to monitor before considering it stable

### Rollback Procedures

**Critical for incident response**:
- How to rollback (commands, UI steps)
- When to rollback vs. fix forward
- How long previous version is available
- Data considerations (migrations that can't be undone)

### Hotfix Process

For emergency deployments:
- Expedited process steps
- Who can approve
- Reduced testing requirements (if any)
- Post-hotfix follow-up

### Anti-patterns to Avoid
- ❌ Don't require tribal knowledge to deploy
- ❌ Don't skip rollback documentation
- ❌ Don't assume deployments always succeed
- ❌ Don't forget to document manual steps

---

## Template

````markdown
# Deployment

## Deployment Overview

| Aspect | Approach |
|--------|----------|
| Frequency | [Continuous/Daily/Weekly/On-demand] |
| Strategy | [Blue-green/Canary/Rolling/All-at-once] |
| Feature flags | [Yes - tool name / No] |
| Typical duration | [X minutes from merge to production] |

## Build Process

```bash
# Build commands
[commands]

# Run tests
[commands]

# Create artifacts
[commands]
```

## CI/CD Pipeline

### Pipeline Stages

| Stage | What Happens | Duration | Trigger |
|-------|--------------|----------|---------|
| Build | [compile, bundle] | [X min] | [auto on push] |
| Test | [unit, integration tests] | [X min] | [auto] |
| Security scan | [SAST, dependency check] | [X min] | [auto] |
| Deploy to staging | [deploy, run migrations] | [X min] | [auto on main] |
| Deploy to production | [deploy, run migrations] | [X min] | [manual approval] |

### Pipeline Location
- **Config file**: [path to CI/CD config]
- **Dashboard**: [link to CI/CD dashboard]
- **Logs**: [where to find logs]

### Approval Gates

| Gate | Who Can Approve | When Required |
|------|-----------------|---------------|
| Production deploy | [roles/people] | [always/for certain changes] |

## Deployment Prerequisites

### Permissions Required
- [List required access/permissions]

### Pre-deployment Checklist
- [ ] [Check 1]
- [ ] [Check 2]
- [ ] Database migrations reviewed (if any)

## Database Migrations

- **When to run**: [before/during/after deployment]
- **Command**: `[migration command]`
- **Rollback**: `[rollback command]`
- **⚠️ Irreversible migrations**: [how to handle]

## Deploy Commands

### Deploy to Staging
```bash
[commands]
```

### Deploy to Production
```bash
[commands]
```

## Verification

### Automated Checks
- Health endpoint: `[URL]` - expect `[response]`
- Smoke tests: `[how to run or where they run]`

### Manual Verification
1. [Check key functionality X]
2. [Check key functionality Y]

### Metrics to Watch
| Metric | Normal Range | Alert Threshold |
|--------|--------------|-----------------|
| Error rate | [X%] | [Y%] |
| Response time | [X ms] | [Y ms] |
| [Custom metric] | [range] | [threshold] |

## Rollback

### When to Rollback
- Error rate exceeds [X%]
- [Critical functionality] is broken
- [Other criteria]

### How to Rollback

```bash
# Rollback commands
[commands]
```

Or via UI: [steps]

### Rollback Considerations
- **Previous version available for**: [duration]
- **Database rollback**: [possible/not possible, steps if possible]
- **Data created during bad deploy**: [how handled]

## Hotfix Process

For emergency fixes that can't wait for normal pipeline:

1. Create branch from `[production branch]`
2. Make fix with minimal changes
3. Get approval from [who]
4. Deploy using [expedited process]
5. Backport to main branch
6. Post-incident: [follow-up requirements]

## Release Process

- **Versioning**: [semver/date-based/other]
- **Changelog**: [where maintained, how updated]
- **Release notes**: [where published]

## Configuration Management

| Config | Where Set | When Applied | Secret? |
|--------|-----------|--------------|---------|
| [Name] | [ENV/ConfigMap/etc.] | [deploy/runtime] | Yes/No |
````

**Auto-discover from**: CI/CD configs (.github/workflows, .gitlab-ci.yml, Jenkinsfile), Makefile, package.json scripts, deployment scripts, Dockerfile
