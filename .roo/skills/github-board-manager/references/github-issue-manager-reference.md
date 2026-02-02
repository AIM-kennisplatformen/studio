# GitHub Issue Manager

A consolidated command-line tool for managing GitHub issues, project boards, and issue relationships in BMAD (Business Modeling & Agent Development) workflows.

## Overview

This tool consolidates all GitHub issue management functionality from the `.bmad-core/scripts/github/` directory into a single, easy-to-use script with sub-commands. It provides comprehensive issue management capabilities including:

- **Epic, sub-epic, feature, and Task Creation**: Create hierarchical issues with automatic labeling and relationships
- **Project Board Management**: Automatically manage GitHub Projects v2 boards with proper status tracking
- **Issue Relationships**: Create and manage sub-issue relationships between epics, sub-epics, features, and tasks
- **Status Management**: Update issue statuses with project board synchronization
- **Markdown Migration**: Migrate existing Markdown issue files to GitHub issues
- **Issue Listing**: List and filter features with advanced search capabilities
- **Validation**: Validate script outputs and operations

## Prerequisites

### Required Tools

#### macOS (using Homebrew)
- **GitHub CLI (gh)**: `brew install gh`
- **jq**: `brew install jq`
- **yq**: `brew install yq`

#### Ubuntu/Debian
- **GitHub CLI (gh)**:
  ```bash
  # Add GitHub CLI repository
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
  sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
  
  # Install GitHub CLI
  sudo apt update
  sudo apt install gh
  ```

- **jq**: `sudo apt install jq`
- **yq**:
  ```bash
  # Install yq (YAML processor)
  sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
  sudo chmod +x /usr/local/bin/yq
  ```

#### Alternative: Using snap (Ubuntu)
```bash
# Install all tools via snap
sudo snap install gh
sudo snap install jq
sudo snap install yq
```

### Authentication

```bash
# Authenticate with GitHub CLI
gh auth login
```

### Project Configuration

Your project must have a `.bmad-core/core-config.yaml` file with GitHub configuration:

```yaml
github:
  repo: "your-org/your-repo"
  project_board: "Your Project Board Name"
```

## Installation

1. Copy `github-issue-manager.sh` to your project root directory
2. Make it executable:
   ```bash
   chmod +x github-issue-manager.sh
   ```

## Usage

```bash
./github-issue-manager.sh <command> [options]
```

## Commands

### Issue Creation Commands

These commands require _slugs_: Derive from title, lowercase, hyphens instead of spaces, alphanumeric and hyphens only, max 20 characters, use well known abbreviations where possible (e.g., "auth" for "authentication"),omit stop words (e.g., "the", "and", "of")


#### `create-epic`
Create an epic issue tpye with project board integration. Features become sub-issues of the epic.

```bash
./github-issue-manager.sh create-epic <title> <body> <epic_slug> <issue_type> [<epic_num> <epic_slug>`]
```

**Parameters:**
- `<title>`: Issue title
- `<body>`: issue description (supports markdown)
- `<issue_slug>`: Required slug for labeling the issue
- `<issue_type>`: GitHub issue type epic
- `--epic <epic_num> <epic_slug>`: Optional flag to link issue to a parent epic


**Examples:**

```bash
# Create a authentication epic
./github-issue-manager.sh create-epic "Authentication and Secure Access for Knowledge Platforms" "

## Description

The end user needs secure access to the platform and needs to be confident that his personal information is treated stored safely and treated in accordance with the GDPR. Furthermore, the authentication process should distribute permission to the data needs to user is allowed access to.

## So that …

As a user of the platform I want to have smooth access to the dataplatform and the data I am allowed access to, and trust that my personal account information is secure and cannot/will not be used for other purposes.

## Attacker Story

As a **malicious actor**, I want to **gain unauthorized access to user accounts or sensitive data**, so that **I can manipulate platform content, exfiltrate user data, or compromise system integrity**.

### Mitigation goals
- Enforce OAuth-based authentication with secure token exchange.
- Store credentials safely if manual authentication is used (hashed and salted passwords).
- Implement rate limiting, session expiration, and monitoring for suspicious activity.

## Acceptance criteria

- [x] #29 
- [x] If OAuth integration is infeasible for Microsoft, implement a secure username–password.
- [ ] Include account management if OAuth is infeasible (password reset, logout, session refresh).
- [ ] Provide an API interface compatible with OAuth and future identity providers.
- [ ] Enforce HTTPS and secure cookie handling across all authentication flows.

## Stakeholders and Users

<!-- This Child Epic was initially reported by the **product owner**.   -->
Stakeholders include **platform users, administrators, and data protection officers**.  
Their interests are maintaining a secure, privacy-compliant platform while ensuring ease of access for verified users to appropriate data (sources).  
Decision-makers are involved, since authentication affects compliance, user onboarding, and long-term platform sustainability.

## The User’s problem

To analyze and summarize the problem:

- Users need a simple, recognizable login method to access the knowledge platform.
- Implementing a consistent authentication system is essential for both security and usability.
- Without centralized authentication, managing permissions and access to verified content becomes fragmented and error-prone.

## The impact of this problem on the User

- **Security**: Without proper authentication, user data and retrieved content could be exposed or misused.
- **Usability**: Complex, unreliable or unfamiliar login processes discourage platform adoption.
- **Trust**: Users expect data protection and privacy compliance as a baseline for credibility.

## The reach of this problem

- Affects all users of the platform, including policy makers, researchers, and project partners.
- Impacts administrators responsible for access management and compliance.

## Business case

If this need is not addressed, this incurs the following **costs** on the organization:

- Increased security risks and potential data breaches.
- Loss of user trust and reduced platform adoption.
- Additional maintenance costs for ad hoc or insecure authentication solutions.

If it is addressed, that will provide **value** in the following way:

- Establishes a secure, scalable and standardized authentication foundation for future features.
- Simplifies user onboarding and enhances collaboration.
<!-- - Demonstrates compliance with privacy and data protection regulations (GDPR). -->

## User studies and supporting materials

<!-- - Planned **user acceptance testing** of login flows with partners. -->
<!-- - **Metrics**: login success rate, OAuth integration success, user satisfaction with sign-up flow. -->
<!-- - Supporting materials:   
  - Technical design for OAuth and fallback mechanisms.  
  - Security review documentation.  
  - Prototype interfaces for authentication flow.  -->
"
# Create a authentication epic
./github-issue-manager.sh create-epic "Epic 2: User Authentication" "

## Description

For expansion of the body of literature (BoL) in the SCEPA app, we want project partners and Community of Interest members to be able to easily upload documents from their respective organizations. This needs to make the content of the platform more self-sustaining in stead of relying solely on centralized and specifically assigned curators.

The interface should give the user the possibility to upload documents and assign the relevant meta and contextual data (such as project, organization, type of documents, etc.). The user should be able to choose from exiting entities or create a new instance of an entity if it doesn't exist yet. It should also give the user the possibility to propose new types or sub-types if the user feels that the uploaded document doesn't adhere to any of the existing types.

---

## So that …  
As a user of the SCEPA-app, I want an easy interface by which I am able to upload documents into the database, so that expert users can keep the repository relevant, share knowledge, and reduce dependence on central curators.

---

## Attacker Story  
As a malicious actor, I want to upload files with hidden malware or unauthorized metadata, so that I can compromise the system or exfiltrate sensitive data.  

**Mitigation:**  
- All uploads must be scanned for malware.  
- Metadata and file type validation must prevent injection or schema corruption.
- Access control rules restrict document upload permissions to authenticated, authorized users.

---

## ✅ Acceptance Criteria  
- [ ] #54 
- [ ] **Existing Entity Selection:** Each field provides a searchable dropdown or autocomplete populated with existing entities from the database.  
- [ ] **Type Suggestion:** If the uploaded document does not fit in any of the existing types in the experience of the user, the user should be able to suggest a new type. The ingestion pipeline should then be transferred to the maintainer of the database for verification and implementation.  
- [ ] **Metadata Integrity:** There is a distinction between mandatory information and optional information.
- [ ] **UI verification**: UI is verified by @VeraLange 
- [ ] **Security:** Uploaded files are scanned for malware and validated for safe content before storage.  
- [ ] **Permissions:** Only authenticated and authorized users (project partners and CoI members) can access the upload functionality.  
- [ ] **Audit Trail:** Each upload event (file, metadata, uploader ID, timestamp) is logged for traceability.
- [ ] **Error Feedback:** If an upload fails, the interface provides clear error messages and suggestions for resolution.
- [ ] **Extensibility:** The upload interface is configurable to accommodate future additions or removals of “TypeDB things” without major redevelopment.
- [ ] **Accessibility:** The interface meets accessibility standards (WCAG 2.1 AA) for usability by all contributors.
- [ ] **Performance:** The upload process (excluding file transfer) should complete within 5 seconds for one document under normal load conditions.


---

## Stakeholders and Users  

- **Stakeholders:**  
  - *Project Partners* – contributing organizations maintaining and expanding the BoL.
  - *Community of Interest (CoI) Members* – subject matter experts contributing documents and metadata.
  - *Database Maintainers / Curators* – reviewing suggested new types or subtypes.
  - *App Administrators* – managing permissions and overall BoL integrity.

This Child Epic was initially reported by **Marijn Siebel** and **validated by partner organizations**.
Decision-makers are **indirectly involved** since they rely on the BoL for knowledge-sharing metrics and community engagement insights.

---

## The User’s Problem  

Currently, only centralized curators can upload documents to the Body of Literature, creating a bottleneck. Contributors from partner organizations or the CoI cannot directly share new publications, reports, or outputs. This makes the updates, limits and the diversity of material more easily available to the community and less labor intensive.

---

## The Impact of this Problem on the User  

This lack of autonomy reduces **knowledge freshness (Quality: Relevance)**, **participation (Quality: Engagement)**, and **efficiency (Quality: Maintainability)**.  
Users experience delays in publication visibility, while curators face increased administrative workload.

---

## The Reach of this Problem  

The problem affects **curators of the BoL**, **maintainers of the database**, all **active partner organizations** and **Community of Interest contributors**

---

## Business Case  

**If not addressed, this incurs costs in:**
- Increased support and maintenance time for central curators.
- Slower knowledge dissemination across projects and partners.
- Creates biasses in the BoL towards expertise and perspective of central curators
- Risk of partner disengagement due to lack of autonomy.  

**If addressed, this provides value through:**
- Increased contribution rates and faster content updates.  
- Reduced curation overhead and centralized maintenance costs.
- Reduces bias in the BoL.
- Higher partner satisfaction and engagement with the SCEPA platform. 
- Strengthened sustainability of the BoL as a living, community-driven resource.  

---

## User Studies and Supporting Materials  

- **User Interviews:** Conducted with 5 project partners and 3 CoI members (April 2026) indicating strong desire for decentralized upload capabilities.

"
```

**Output:**
```json
```

#### `create-feature`
Create an feature feature type, linked to a parent epic.

```bash
./github-issue-manager.sh create-feature <title> <body> <issue_slug> <issue_type> [--epic <epic_num> <epic_slug>]
```

**Parameters:**
- `<title>`: issue title
- `<body>`: issue description (supports markdown)
- `<issue_slug>`: Required slug for labeling the issue
- `<issue_type>`: GitHub issue type
- `--epic <epic_num> <epic_slug>`: Optional flag to link issue to a parent epic

**Examples:**

```bash
# Create a feature linked to an epic
./github-issue-manager.sh create-feature "Improve graph positioning algorithm or replace with an alternative to suit our use case" "

## Description

The positions of the vertices and edges are now all over the place and impede the intended functionality off making information more easily and efficiently accessible. The hypergraph structure needs to be represented in a way that helps the user in steads of confuses/overloads. At the least, the hypergraph structure should be represented in such a way that makes it's logic understandable so we can research if and what value it could have in answering (complex) questions.

For this end we need an positioning algorithm that unfolds the graph structure sequentially, maintaining screen positions of previously visited vertices and edges. If existing/available algorithms are not (relatively) easily available, we should look for alternatives. 

Hard coding could be a temporary short-cut for the deployed SCEPA app, as it the KG is now very small.

## ..., so that...

As a user I want the graph interface and it's elements to provide clarity and insight into the information I am gathering iso confusion and chaos in my screen, so that the graph enhances my experience instead of hampering it.

## Acceptance criteria


<!--Choose acceptance criteria from the acceptance criteria library.-->

<!--Add specific acceptance criteria where needed.-->

1. [ ] Edges can't cross each other
2. [ ] Type hierarchy of the KG is preserved and recognizably displayed
3. [ ] Relative positions of vertices are maintained throughout the user experience
4. [ ] The graph "unfolds" it's next hop when a vertice is clicked
"

# Create a fundamental documentation feature linked to epic #15
./github-issue-manager.sh create-feature "OAuth authentication through SURF" "

## Description
For the HAN-knowledge platform we are going to implement OAuth authentication with your HAN-account, but using SURF's authentication protocols. Due to the bureaucratic and "up-tight" character of the the HAN as an organization, it is a very cumbersome process to directly authenticate users and according data access. Trough SURF we can easily circumvent this and achieve the desired end result: automatic authentication using OAuth with your HAN-account and have have data access distributed accordingly.

## ..., so that...

As a user I want to access the platform using my Microsoft HAN-account, so that have automated access to the data I'm allowed to access.

## Acceptance criteria


1. [ ] OAuth registration
2. [ ] Data access is translated into TypeDB
3. [ ] ...
4. [ ] ...
"
```

**Output:**
```json
```

#### `create-task`
Create a task issue type. Requires a linked parent feature issue type.

```bash
./github-issue-manager.sh create-task <title> <body> <issue_slug> <issue_type> 
```

**Parameters:**
- `<title>`: issue title
- `<body>`: issue description (supports markdown)
- `<issue_slug>`: Required slug for labeling the issue
- `<issue_type>`: GitHub issue type

**Examples:**

```bash
./github-issue-manager.sh create-task "Quick security patch" "
## Task Description
Apply urgent security patch to address vulnerability CVE-2024-1234.

## Requirements
- Update dependency to latest version
- Test for regressions
- Deploy to production
"

./github-issue-manager.sh create-task "Setup CI/CD Pipeline" "
## Task Description
Configure GitHub Actions for automated testing and deployment.

## Requirements
- Build pipeline
- Test automation
- Deploy to staging environment
"

./github-issue-manager.sh create-task "Create Registration Form UI" "

## Task Description
Design and implement the user registration form with proper validation and user experience.

## Requirements
- React component with form validation
- Responsive design for mobile/desktop
- Real-time validation feedback
- Accessible form elements
- Loading states during submission
"
```

**Output:**
```json
```

### Issue Management Commands

#### `update-status`
Update issue status in the project board.

```bash
./github-issue-manager.sh update-status <issue_num> <status>
```

**Available Statuses:**
- `Todo` (or legacy: `Backlog`, `Next Milestone`, `Ready`)
- `In Progress`
- `Done` (or legacy: `Review`, `Done`)

**Examples:**

```bash
# Start working on an issue
./github-issue-manager.sh update-status 16 "In Progress"

# Complete an issue
./github-issue-manager.sh update-status 17 "Done"

# Move issue back to backlog
./github-issue-manager.sh update-status 18 "Todo"

# Using legacy status names (backwards compatible)
./github-issue-manager.sh update-status 19 "Backlog"
./github-issue-manager.sh update-status 20 "Review"
```

**Output:**
```json
{"success": "Issue status updated to In Progress", "item_id": "PVTI_789", "original_column": "In Progress"}
```

### Query Commands

#### `list-features`
List features with optional filtering.

```bash
./github-issue-manager.sh list-features [filter]
```

**Filter Options:**
- `state:open issue_type:epic, sub-epic, feature or task` (default)
- `state:closed issue_type:epic, sub-epic, feature or task`
- `issue_type:epic, sub-epic, feature or task`
- `state:open`
- `state:closed`

**Examples:**

```bash
# List all open issues (default)
./github-issue-manager.sh list-issues

# List closed epics
./github-issue-manager.sh list-issues "issue_type:epic state:closed"

# List all open features
./github-issue-manager.sh list-issues "issue_type:feature state:open"

# List all open issues
./github-issue-manager.sh list-issuess "state:open"
```

**Example Output:**
```json
[
  {
    "number": 16,
    "title": "User Registration",
    "body": "## Descritption\nAs a new user...",
    "issue_type": "sub-epic",
    "parent_relation": {
      "name": "epic_title"}
    ],
    "assignees": []
  },
  {
    "_metadata": {
      "filter": "issue_type:feature state:open",
      "count": 1
    }
  }
]
```

### Migration Commands

#### `migrate-features`
Migrate existing Markdown issue files to GitHub issues.

```bash
./github-issue-manager.sh migrate-features
```

This command will:
1. Scan `docs/features/` for `.md` files
2. Parse filenames in format `{epic}.{issue}.{title}.md`
3. Create epic issues for each unique epic number
4. Create issues from markdown content
5. Establish parent-child relationships
6. Generate a detailed migration log

**Example Structure:**
```
docs/features/
├── 1.1.repository-setup.md
├── 1.2.ci-cd-pipeline.md
├── 2.1.user-registration.md
└── 2.2.user-login.md
```

**Example Output:**
```json
{
  "success": "Migration completed",
  "epic_count": 2,
  "issue_count": 4,
  "log_file": "migration-log-20240124-143022.json",
  "issues_dir": "/path/to/docs/issues"
}
```

**Migration Log Format:**
```json
{
  "migration_started": "2024-01-24T14:30:22+01:00",
  "results": [
    {
      "type": "epic",
      "file": "Epic 1",
      "issue_number": 15,
      "status": "created",
      "message": "Epic migrated successfully",
      "timestamp": "2024-01-24T14:30:23+01:00"
    },
    {
      "type": "issue",
      "file": "1.1.repository-setup.md",
      "issue_number": 16,
      "status": "created",
      "message": "Issue migrated successfully",
      "timestamp": "2024-01-24T14:30:24+01:00"
    }
  ],
  "migration_completed": "2024-01-24T14:30:30+01:00"
}
```

### Utility Commands

#### `help`
Show usage information.

```bash
./github-issue-manager.sh help
./github-issue-manager.sh -h
./github-issue-manager.sh --help
```

#### `version`
Show version information.

```bash
./github-issue-manager.sh version
./github-issue-manager.sh -v
./github-issue-manager.sh --version
```

## Workflow Examples

### Complete Epic Creation Workflow

```bash
#!/bin/bash

# 1. Create an epic
EPIC_RESULT=$(./github-issue-manager.sh create-epic "Epic 3: Data Management" "
This epic covers all data-related functionality including:
- Database design and setup
- Data models and relationships
- Data validation and integrity
- Backup and recovery procedures
" "data-management")

EPIC_NUM=$(echo "$EPIC_RESULT" | jq -r '.epic_number')
echo "Created Epic #$EPIC_NUM"

# 2. Create features for the epic (using new syntax)
ISSUE1_RESULT=$(./github-issue-manager.sh create-feature "OAuth authentication through SURF" "
## Description

For the HAN-knowledge platform we are going to implement OAuth authentication with your HAN-account, but using SURF's authentication protocols. Due to the bureaucratic and "up-tight" character of the the HAN as an organization, it is a very cumbersome process to directly authenticate users and according data access. Trough SURF we can easily circumvent this and achieve the desired end result: automatic authentication using OAuth with your HAN-account and have have data access distributed accordingly.

## ..., so that...

As a user I want to access the platform using my Microsoft HAN-account, so that have automated access to the data I'm allowed to access.

## Acceptance criteria


<!--Choose acceptance criteria from the acceptance criteria library.-->

<!--Add specific acceptance criteria where needed.-->

1. [ ] OAuth registration
2. [ ] Data access is translated into TypeDB
3. [ ] ...
4. [ ] ...
" "OAuth authentication through SURF" --epic $EPIC_NUM "OAUTH")

ISSUE1_NUM=$(echo "$ISSUE1_RESULT" | jq -r '.issue_number')
echo "Created issue #$ISSUE1_NUM"

# 3. Create tasks for the issue (using new syntax)
./github-issue-manager.sh create-task "Create ER Diagram" "
Design entity relationship diagram showing all tables, relationships, and constraints.
" --issue $ISSUE1_NUM "OAuth authentication through SURF" --epic-slug "OAUTH"

./github-issue-manager.sh create-task "Write Migration Scripts" "
Create database migration scripts for initial schema setup.
" --issue $ISSUE1_NUM "OAuth authentication through SURF" --epic-slug "OAUTH"

# 4. Start working on the epic
./github-issue-manager.sh update-status $EPIC_NUM "In Progress"

echo "Epic workflow created successfully!"
```

### Bulk Issue Status Updates

```bash
#!/bin/bash

# Move all completed tasks to Done status
COMPLETED_TASKS=(17 18 19 20)

for task in "${COMPLETED_TASKS[@]}"; do
    echo "Updating task #$task to Done..."
    ./github-issue-manager.sh update-status $task "Done"
done

# Move features ready for review
REVIEW_FEATURES=(16 21)

for issue in "${REVIEW_FEATURES[@]}"; do
    echo "Moving issue #$issue to Done..."
    ./github-issue-manager.sh update-status $issue "Done"
done
```

## Configuration

### Core Configuration File

Your `.bmad-core/core-config.yaml` should include:

```yaml
github:
  repo: "your-organization/your-repository"
  project_board: "Your Project Board Name"

# Optional: Additional BMAD configuration
prd:
  prdLocation: "docs/prd"
  
architecture:
  architectureLocation: "docs/architecture"
  
qa:
  qaLocation: "docs/qa"
```

### Project Board Setup

The script automatically:
- Links your repository to the project
- Sets up proper field mapping for status transitions

### Github issue type management

The script automatically manages these existing Github issue types:
- `epic` - All epic issues
- `sub-epic` - All sub-epic issues
- `feature` - All featuer issues
- `Task` - All task issues

### Github issue relationship management
The script automatically manages relations between issue types:
- `epic` and `sub-epic` - A sub-epic needs to have a parent epic
- `epic` and `feature` - All epics need to be broken down into sub-epics and/or features as sub-issues
- `sub-epic` and `feature`- All sub epics need to be broken down into features as sub-issues
- `feature` and `task` - All features need to be broken down into tasks as sub-issues

## Troubleshooting

### Common Issues

#### "GitHub CLI not authenticated"
```bash
gh auth login
```

#### "core-config.yaml not found"
Ensure you have a `core-config.yaml` file in your .roo/skills folder with proper GitHub configuration.

#### "Invalid repo format"
Ensure your repo is specified as `owner/repository` in the configuration file.

#### "Status field not found in project"
The script expects a default "Status" field in your GitHub project. This is created automatically in new projects.

#### "Failed to create project"
Ensure you have proper permissions in the organization/repository to create projects.

### Debug Mode

For verbose output, you can modify the script to show more details:

```bash
# Add debug output by uncommenting log_info statements
# or redirect stderr to see all log messages
./github-issue-manager.sh create-epic "Test" "Test" 2>&1
```

### Result Validation

You can validate operation results using standard JSON parsing:

```bash
RESULT=$(./github-issue-manager.sh create-epic "Important Epic" "Critical work" "important")
if echo "$RESULT" | jq -e '.epic_number' >/dev/null 2>&1; then
    echo "Epic created successfully"
    EPIC_NUM=$(echo "$RESULT" | jq -r '.epic_number')
    echo "Epic number: $EPIC_NUM"
else
    echo "Epic creation failed"
    exit 1
fi
```

## Migration from Individual Scripts

If you were previously using individual scripts from `.bmad-core/scripts/github/`, here's the mapping:

| Old Script | New Command |
|------------|-------------|
| `create-epic-issue.sh` | `create-epic` |
| `create-feature-issue.sh` | `create-feature` |
| `create-task-issue.sh` | `create-task` |
| `update-issue-status.sh` | `update-status` |
| `list-features.sh` | `list-features` |
| `migrate-md-to-issues.sh` | `migrate-features` |

**Internal Utilities (no longer user commands):**
- `load-config.sh` - Now internal configuration loading
- `ensure-project-board.sh` - Now automatic project board setup
- `create-sub-issue-relationship.sh` - Now automatic relationship creation
- `validate-operation.sh` - Use standard JSON validation tools instead

### Batch Migration Script

```bash
#!/bin/bash
# Replace old script calls with new consolidated commands

# Old way:
# .bmad-core/scripts/github/create-epic-issue.sh "Epic Title" "Epic Body"

# New way:
./github-issue-manager.sh create-epic "Epic Title" "Epic Body" "epic-slug"

# Old way:
# .bmad-core/scripts/github/update-issue-status.sh 42 "In Progress"

# New way:
./github-issue-manager.sh update-status 42 "In Progress"
```

## Contributing

When adding new functionality:

1. Add the function in the appropriate section
2. Add the command case in the `main()` function
3. Update the usage help text
4. Add examples to this README
5. Test all functionality thoroughly

## Support

For issues with this tool:
1. Verify all prerequisites are installed
2. Check your configuration file
3. Test GitHub CLI authentication
4. Review error messages in the output
5. Check GitHub repository permissions

## License

This tool is part of the BMAD framework. See project license for details.