# Epic: Expertise Mining via Microsoft Graph API

## Description

As a user of the knowledge platform, I want to discover expertise within our organization by mining data from Microsoft Graph API (People, Teams, SharePoint), so that the RAG component can provide answers about who knows what, who has worked on similar topics, and connect me with relevant colleagues.

This epic introduces Microsoft Graph API as a new data source for the existing RAG system, complementing the current literature-based sources (Zotero, TypeDB) with organizational knowledge derived from employee activities.

## So that...

As a researcher or knowledge worker, I want to find colleagues with relevant expertise based on their activities, documents, team collaborations, and profile information, so that I can accelerate knowledge sharing, reduce duplication of effort, and build on existing organizational expertise rather than starting from scratch.

## Attacker Story

As a **malicious actor or insider threat**, I want to **exploit the Graph API integration to access sensitive personal data, emails, or documents beyond my authorization level**, so that **I can exfiltrate confidential information or violate privacy boundaries**.

### Mitigation goals

- Implement least-privilege OAuth scopes - only request permissions strictly necessary for expertise mining
- Anonymize or aggregate personal activity data before storing in the knowledge graph
- Apply data classification to filter out confidential documents/communications
- Ensure GDPR compliance with consent mechanisms and data retention policies
- Audit all Graph API access and flag anomalous query patterns

## Acceptance Criteria

1. [ ] **Graph API Integration**: Microsoft Graph API client is implemented with OAuth 2.0 authentication
2. [ ] **People Data Extraction**: Employee profiles, skills, and organizational relationships are extracted
3. [ ] **Teams Mining**: Collaboration patterns from Teams channels and conversations are analyzed (metadata only, not content)
4. [ ] **SharePoint Indexing**: Relevant SharePoint documents are indexed for expertise indicators (authors, topics, tags)
5. [ ] **RAG Integration**: Extracted expertise data is available to the RAG component via MCP tools
6. [ ] **Privacy Compliance**: GDPR-compliant consent and data handling mechanisms are in place
7. [ ] **Query Capability**: Users can ask "Who is an expert in X?" and receive relevant colleague suggestions

## Stakeholders and Users

This Epic was initially reported by the **product team** in collaboration with **HAN knowledge platform stakeholders**.

**Stakeholders:**
- **Knowledge workers** - Primary users seeking expertise within the organization
- **HR/Talent management** - Interest in skill mapping and expertise discovery
- **Data Protection Officers** - Ensuring privacy compliance
- **IT Security** - Managing OAuth credentials and API access
- **Researchers** - Finding collaborators for projects

Decision-makers are **involved**, since this connects to organizational data governance policies and Microsoft 365 tenant administration.

## The User's Problem

To analyze and summarize the problem:

- Users cannot easily discover who in the organization has expertise in specific topics
- Knowledge is siloed in individual Teams channels, SharePoint sites, and email threads
- No unified way to query organizational expertise alongside literature/research knowledge
- Manual networking and asking around is slow and incomplete

## The Impact of this Problem on the User

- **Efficiency**: Time lost searching for experts or reinventing solutions that colleagues have already developed
- **Collaboration**: Missed opportunities for cross-team knowledge sharing
- **Quality**: Suboptimal decisions due to lack of awareness of internal expertise
- **Onboarding**: New employees struggle to find the right people for guidance

## The Reach of this Problem

- Affects all knowledge workers in the organization
- Most impactful for:
  - New employees seeking guidance
  - Project teams looking for subject matter experts
  - Researchers seeking collaborators
  - Managers building project teams

## Business Case

If this need is not addressed, this incurs the following **costs**:

- Duplicated research efforts across teams
- Slower project initiation due to expert discovery friction
- Knowledge attrition when experts leave without knowledge transfer
- Suboptimal team composition for projects

If it is addressed, that will provide **value** in the following way:

- Faster expert discovery (seconds vs. days)
- Improved knowledge sharing and reduced silos
- Better project team formation based on actual expertise
- Enhanced RAG responses that include "who to ask" alongside "what to read"
- Strengthens the knowledge platform as a comprehensive expertise system

## User Studies and Supporting Materials

- **Planned**: User interviews to validate expertise discovery pain points
- **Metrics**: Time-to-expert, query success rate, user satisfaction
- **Related work**: Existing implementations in enterprise knowledge management systems

## Related Issues

- #10 - RAG evaluation (this adds a new data source to evaluate)
- #14 - Natural language to database queries (expertise queries will use this)
- #50 - OAuth authentication through SURF (may share authentication patterns)

---

## Candidate User Stories

*To be refined after epic approval:*

1. **Graph API Client Setup**: Implement Microsoft Graph API client with OAuth 2.0 flow
2. **People Profile Extraction**: Extract and index employee profiles and declared skills
3. **Teams Collaboration Mining**: Analyze Teams channel participation for expertise signals
4. **SharePoint Document Indexing**: Index SharePoint documents by author and topic
5. **Expertise MCP Tool**: Create MCP tool for querying expertise from the knowledge graph
6. **Privacy & Consent Layer**: Implement GDPR-compliant consent and anonymization
7. **Expertise Query UI**: Add "Find Expert" capability to the frontend
