# Infrastructure Section Template

**Purpose**: Document the physical/virtual hardware and runtime environment. This is what someone needs to understand where software runs and how components are connected.

## Guidance

### What This Section Should Accomplish
- Help developers understand the runtime topology
- Enable operations to manage and troubleshoot the system
- Document security boundaries and access controls
- Provide context for capacity planning and scaling decisions

### Runtime Topology

Document what runs where:
- Which components run on which servers/containers
- How many instances of each component
- Geographic distribution if applicable
- Scaling configuration (auto-scaling rules, min/max instances)

### Network Architecture

- How components communicate (internal networks, service mesh)
- Security boundaries (VPCs, subnets, firewalls)
- Load balancing strategy
- DNS and service discovery
- CDN configuration

### High Availability

- Redundancy setup (multi-AZ, multi-region)
- Failover mechanisms
- Single points of failure (and mitigation)
- Disaster recovery site if applicable

### Environment Parity

Document differences between environments:
- What's the same across dev/staging/production?
- What's different and WHY?
- Which differences have caused production bugs?

**Goal**: Minimize surprises when deploying to production.

### Infrastructure as Code

- Where IaC lives (Terraform, CloudFormation, Pulumi, Ansible)
- How to provision new environments
- State management (where state is stored)
- Drift detection approach

### Local Development Setup

Enable developers to run the system locally:
- Docker Compose or similar orchestration
- Which services run locally vs. connect to shared resources
- How to stub/mock external services
- Performance differences from production

### Environment Variables

Group variables by purpose and document clearly:
- **Application config**: Feature flags, timeouts, limits
- **Service connections**: Database URLs, API endpoints
- **Secrets**: API keys, passwords (NEVER document values!)
- **Environment-specific**: Values that change between environments

Document:
- Dependencies between variables
- Which variables are secrets (mark clearly)
- Example values for non-secrets
- Where secrets are managed (Vault, AWS Secrets Manager, etc.)

### Anti-patterns to Avoid
- ❌ Don't document secret values - ever
- ❌ Don't assume readers know your cloud provider's UI
- ❌ Don't skip local development setup
- ❌ Don't ignore environment differences that cause issues

---

## Template

```markdown
# Infrastructure

## Environments Overview

| Environment | Purpose | URL | Notes |
|-------------|---------|-----|-------|
| Local | Developer machines | localhost:3000 | [Docker Compose/direct] |
| Development | Shared dev environment | [URL] | [if applicable] |
| Staging | Pre-production testing | [URL] | [production-like?] |
| Production | Live system | [URL] | [region/zones] |

### Environment Parity

| Aspect | Local | Staging | Production |
|--------|-------|---------|------------|
| Database | [SQLite/Docker PostgreSQL] | [Managed PostgreSQL] | [Managed PostgreSQL] |
| [Aspect] | [local approach] | [staging approach] | [production approach] |

**Known differences that matter**: [list any gotchas]

## Infrastructure Diagram

[Diagram showing servers, containers, networks, and how they connect]

## Runtime Topology

| Component | Runs On | Instances | Auto-scaling |
|-----------|---------|-----------|--------------|
| [Web app] | [ECS/K8s/VM] | [count] | [min-max or N/A] |
| [API] | [ECS/K8s/VM] | [count] | [min-max or N/A] |
| [Worker] | [ECS/K8s/VM] | [count] | [min-max or N/A] |

## Cloud Resources

| Resource | Service | Purpose | Environment |
|----------|---------|---------|-------------|
| [Name] | [AWS/GCP/Azure service] | [What it does] | [All/Prod only] |

## Networking

### Network Architecture
- **VPC/Network**: [setup description]
- **Subnets**: [public/private arrangement]
- **Security groups/Firewalls**: [key rules]

### Load Balancing
- **Type**: [ALB/NLB/Cloud Load Balancer]
- **Health checks**: [what's checked]
- **SSL termination**: [where]

### CDN
- **Provider**: [CloudFront/Cloudflare/etc.]
- **What's cached**: [static assets, API responses?]
- **Cache invalidation**: [approach]

## High Availability

- **Redundancy**: [multi-AZ, multi-region]
- **Failover**: [automatic/manual, how it works]
- **Single points of failure**: [identified risks and mitigation]

## Infrastructure as Code

- **Tool**: [Terraform/CloudFormation/Pulumi]
- **Location**: [path to IaC files]
- **State storage**: [S3 bucket, Terraform Cloud, etc.]
- **How to apply**: [commands or CI/CD reference]

## Local Development Setup

### Prerequisites
- [Docker, Node.js version, etc.]

### Quick Start
```bash
# [commands to start local environment]
```

### Local Services
| Service | Local Approach |
|---------|---------------|
| Database | [Docker container / SQLite] |
| Cache | [Docker Redis / in-memory] |
| [External API] | [Mock server / sandbox environment] |

## Environment Variables

### Application Configuration

| Variable | Purpose | Example | Env-specific? |
|----------|---------|---------|---------------|
| `LOG_LEVEL` | Logging verbosity | `info` | Yes |
| `FEATURE_X_ENABLED` | Feature flag | `true` | Yes |

### Service Connections

| Variable | Purpose | Example | Env-specific? |
|----------|---------|---------|---------------|
| `DATABASE_URL` | Database connection | `postgresql://localhost:5432/app` | Yes |
| `REDIS_URL` | Cache connection | `redis://localhost:6379` | Yes |

### Secrets (⚠️ NEVER commit values)

| Variable | Purpose | Managed In |
|----------|---------|------------|
| `API_SECRET_KEY` | [purpose] | [Vault/AWS Secrets Manager] |
| `DATABASE_PASSWORD` | [purpose] | [Vault/AWS Secrets Manager] |

### Variable Dependencies

[Document any variables that depend on others or must be set together]
```

**Auto-discover from**: docker-compose.yml, k8s manifests, terraform, cloudformation, env files, CI/CD configs
