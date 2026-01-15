# Data Section Template

**Purpose**: Document where data lives, how it flows, and how it's managed. This covers ALL data: databases, files, assets, blobs, ML models, and more.

## Guidance

### What This Section Should Accomplish
- Help developers understand where data lives and why
- Clarify data ownership (which component owns which data)
- Document data flows and transformation points
- Address compliance and sensitivity concerns
- Enable developers to set up local environments with appropriate data

### Types of Data Storage

**Databases (relational and NoSQL)**
- Document rationale for database choices
- Key entities and relationships (don't reproduce full schema)
- Non-obvious denormalization decisions
- Indexing strategy for performance-critical queries

**File Systems and Object Storage**
- What types of files are stored (documents, exports, logs)
- Directory structure and naming conventions
- Retention and cleanup policies
- Local vs. cloud storage decisions

**Asset Management**
- Where static assets live (images, fonts, icons)
- Asset pipeline (how assets are processed, optimized)
- CDN configuration if applicable
- Versioning strategy for assets

**Blob Storage (S3, Azure Blob, GCS)**
- Bucket organization and naming
- Access patterns (public, signed URLs, private)
- Lifecycle policies (archival, deletion)
- Cross-region replication if applicable

**Multimedia Content**
- Storage location for audio, video, images
- Transcoding and processing pipelines
- Streaming vs. download approaches
- Thumbnail/preview generation

**ML and Data Science Data**
- Training data location and format
- Model artifacts storage and versioning
- Feature stores if applicable
- Data labeling and annotation storage
- Experiment tracking data

**Caching Layers**
- What is cached and where (Redis, Memcached, in-memory)
- Cache invalidation strategies
- TTL policies

### Data Ownership and Sensitivity

- Which service/component owns which data?
- Data sensitivity classification (PII, financial, health, confidential)
- Who can access what? (roles, services)
- GDPR/compliance considerations (right to deletion, data portability)

### Data Lifecycle

- How data enters the system
- Retention policies: how long is data kept?
- Archival strategies for old data
- Deletion/purging procedures

### Seed Data and Test Data

**Seed data** (for development/staging environments):
- What seed data exists and where it's stored
- How to load seed data
- How to reset to a clean state
- Differences between environments

**Test data**:
- How test data is generated or sourced
- Fixtures and factories
- Data anonymization for production-like test data
- Cleanup after tests

### Anti-patterns to Avoid
- ❌ Don't reproduce full schema documentation - link to it
- ❌ Don't skip data ownership clarity
- ❌ Don't forget about caching strategies and invalidation
- ❌ Don't ignore data sensitivity classification
- ❌ Don't leave seed/test data undocumented

---

## Template

```markdown
# Data

## Data Stores Overview

| Store | Type | Purpose | Owner |
|-------|------|---------|-------|
| [Name] | PostgreSQL/MongoDB/etc. | [What's stored] | [Service/team] |
| [Name] | S3/GCS/Azure Blob | [What's stored] | [Service/team] |
| [Name] | Redis/Memcached | [What's cached] | [Service/team] |
| [Name] | File system | [What's stored] | [Service/team] |

## Database Model

[High-level ERD for core entities - don't include every table]

### Key Entities

#### [Entity Name]
- **Purpose**: [what this represents]
- **Key fields**: [important fields, not all]
- **Relationships**: [connections to other entities]
- **Lifecycle**: [created/updated/deleted when]

## File and Asset Storage

### [Storage Name, e.g., "User Uploads"]
- **Location**: [path or bucket]
- **File types**: [what's stored]
- **Naming convention**: [pattern]
- **Retention**: [how long kept]
- **Access**: [public/private/signed URLs]

## ML/Data Science Data

### Training Data
- **Location**: [where stored]
- **Format**: [file format, schema]
- **Size**: [approximate]
- **Update frequency**: [how often refreshed]

### Model Artifacts
- **Location**: [where models are stored]
- **Versioning**: [how versions are tracked]

## Caching

| Cache | Technology | What's Cached | TTL | Invalidation |
|-------|------------|---------------|-----|--------------|
| [Name] | [Redis/etc.] | [Data type] | [Duration] | [Strategy] |

## Data Flows

[Describe how data moves through the system - consider a diagram]

1. Data enters via [source]
2. Processed by [component]
3. Stored in [destination]
4. Cached in [cache] for [purpose]

## Data Sensitivity

| Data Type | Classification | Special Handling |
|-----------|---------------|------------------|
| [User emails] | PII | [Encrypted, access logged] |
| [Payment info] | Financial/PCI | [Tokenized, not stored] |

## Seed Data

- **Location**: [path to seed files/scripts]
- **Load command**: `[command]`
- **Reset command**: `[command]`
- **Environments**: [which environments use seed data]

## Test Data

- **Fixtures location**: [path]
- **Factory pattern**: [if used, where]
- **Production data**: [how anonymized, if used]

## Migrations

- **Strategy**: [approach - e.g., forward-only, versioned]
- **Location**: [path to migrations]
- **Run command**: `[command]`
- **Rollback approach**: [if supported]

## Backup and Recovery

- **Backup frequency**: [schedule]
- **Retention**: [how long backups kept]
- **Recovery procedure**: [link or brief steps]
- **RTO/RPO**: [targets, link to Quality Attributes]
```

**Auto-discover from**: Schema files, ORM models, migrations, database configs, env vars, S3/storage configs, seed scripts, test fixtures
