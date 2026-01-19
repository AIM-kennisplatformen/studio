# GitHub Issue Manager

A consolidated command-line tool for managing GitHub issues, project boards, and issue relationships in BMAD (Business Modeling & Agent Development) workflows.

## Overview

This tool consolidates all GitHub issue management functionality from the `.bmad-core/scripts/github/` directory into a single, easy-to-use script with sub-commands. It provides comprehensive issue management capabilities including:

- **Epic, Story, and Task Creation**: Create hierarchical issues with automatic labeling and relationships
- **Project Board Management**: Automatically manage GitHub Projects v2 boards with proper status tracking
- **Issue Relationships**: Create and manage sub-issue relationships between epics, stories, and tasks
- **Status Management**: Update issue statuses with project board synchronization
- **Markdown Migration**: Migrate existing Markdown story files to GitHub issues
- **Story Listing**: List and filter stories with advanced search capabilities
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
Create an epic issue with project board integration. Stories become sub-issues of the epic.

```bash
./github-issue-manager.sh create-epic <title> <body> <epic_slug>
```

**Examples:**

```bash
# Create a foundation epic
./github-issue-manager.sh create-epic "Epic 1: Foundation & Infrastructure" "
This epic covers all foundational work including:
- Repository setup
- CI/CD pipeline
- Basic infrastructure
- Development environment
" "foundation"

# Create a feature epic
./github-issue-manager.sh create-epic "Epic 2: User Authentication" "
Complete user authentication system including:
- User registration
- Login/logout
- Password reset
- Multi-factor authentication
" "authentication"
```

**Output:**
```json
{"epic_number": 15}
```

#### `create-story`
Create a story issue, optionally linked to a parent epic.

```bash
./github-issue-manager.sh create-story <title> <body> <story_slug> [--epic <epic_num> <epic_slug>]
```

**Parameters:**
- `<title>`: Story title
- `<body>`: Story description (supports markdown)
- `<story_slug>`: Required slug for labeling the story
- `--epic <epic_num> <epic_slug>`: Optional flag to link story to a parent epic

**Examples:**

```bash
# Create a standalone story (not linked to any epic)
./github-issue-manager.sh create-story "Bug Fix: Login Timeout" "
## Story
As a user, I want the login timeout issue fixed so that I don't get logged out unexpectedly.

## Acceptance Criteria
- [ ] Session timeout extended to 24 hours
- [ ] User is warned before session expiry
- [ ] Active users are not logged out
" "login-timeout-fix"

# Create a story linked to an epic
./github-issue-manager.sh create-story "User Registration" "
## Story
As a new user, I want to register an account so that I can access the application.

## Acceptance Criteria
- [ ] User can enter email, username, and password
- [ ] Email validation is performed
- [ ] Password meets security requirements
- [ ] Registration confirmation is sent via email
- [ ] User is redirected to dashboard after registration

## Tasks
- Setup registration form UI
- Implement validation logic
- Create user database schema
- Setup email service integration
- Add registration API endpoint
" "user-registration" --epic 15 "authentication"

# Create a login story linked to epic #15
./github-issue-manager.sh create-story "User Login" "
## Story
As a registered user, I want to login to my account so that I can access my personal dashboard.

## Acceptance Criteria
- [ ] User can enter email and password
- [ ] Invalid credentials show appropriate error
- [ ] Successful login redirects to dashboard
- [ ] Session is maintained across browser refreshes
- [ ] Remember me option is available

## Tasks
- Create login form UI
- Implement authentication logic
- Setup session management
- Add login API endpoint
- Handle password reset flow
" "user-login" --epic 15 "authentication"
```

**Output:**
```json
{"story_number": 16}
```

#### `create-task`
Create a task issue, optionally linked to a parent story and/or labeled with an epic.

```bash
./github-issue-manager.sh create-task <title> <body> [--story <story_num> <story_slug>] [--epic-slug <epic_slug>]
```

**Parameters:**
- `<title>`: Task title
- `<body>`: Task description (supports markdown)
- `--story <story_num> <story_slug>`: Optional flag to link task to a parent story
- `--epic-slug <epic_slug>`: Optional flag to add epic label without creating a sub-issue relationship

**Examples:**

```bash
# Create a standalone task (not linked to any story or epic)
./github-issue-manager.sh create-task "Quick security patch" "
## Task Description
Apply urgent security patch to address vulnerability CVE-2024-1234.

## Requirements
- Update dependency to latest version
- Test for regressions
- Deploy to production
"

# Create a task with epic label only (good for cross-cutting concerns)
./github-issue-manager.sh create-task "Setup CI/CD Pipeline" "
## Task Description
Configure GitHub Actions for automated testing and deployment.

## Requirements
- Build pipeline
- Test automation
- Deploy to staging environment
" --epic-slug "foundation"

# Create a task linked to a parent story
./github-issue-manager.sh create-task "Create Registration Form UI" "
## Task Description
Design and implement the user registration form with proper validation and user experience.

## Requirements
- React component with form validation
- Responsive design for mobile/desktop
- Real-time validation feedback
- Accessible form elements
- Loading states during submission

## Acceptance Criteria
- [ ] Form validates email format
- [ ] Password strength indicator
- [ ] Form submission shows loading state
- [ ] Error messages are user-friendly
- [ ] Form is accessible (ARIA labels)
" --story 16 "user-registration"

# Create a task with both story link and epic label
./github-issue-manager.sh create-task "Implement Registration API Endpoint" "
## Task Description
Create secure API endpoint for user registration with proper validation and error handling.

## Requirements
- POST /api/auth/register endpoint
- Input validation and sanitization
- Password hashing with bcrypt
- Email uniqueness check
- Rate limiting protection

## Acceptance Criteria
- [ ] Validates all input fields
- [ ] Returns appropriate HTTP status codes
- [ ] Passwords are securely hashed
- [ ] Duplicate email handling
- [ ] API documentation updated
" --story 16 "user-registration" --epic-slug "authentication"
```

**Output:**
```json
{"task_number": 17}
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

#### `list-stories`
List stories with optional filtering.

```bash
./github-issue-manager.sh list-stories [filter]
```

**Filter Options:**
- `label:story state:open` (default)
- `label:story state:closed`
- `label:epic state:open`
- `state:open`
- `state:closed`

**Examples:**

```bash
# List all open stories (default)
./github-issue-manager.sh list-stories

# List closed stories
./github-issue-manager.sh list-stories "label:story state:closed"

# List all open epics
./github-issue-manager.sh list-stories "label:epic state:open"

# List all open issues
./github-issue-manager.sh list-stories "state:open"
```

**Example Output:**
```json
[
  {
    "number": 16,
    "title": "User Registration",
    "body": "## Story\nAs a new user...",
    "labels": [
      {"name": "story"},
      {"name": "epic:authentication"},
      {"name": "story:user-registration"}
    ],
    "assignees": []
  },
  {
    "_metadata": {
      "filter": "label:story state:open",
      "count": 1
    }
  }
]
```

### Migration Commands

#### `migrate-stories`
Migrate existing Markdown story files to GitHub issues.

```bash
./github-issue-manager.sh migrate-stories
```

This command will:
1. Scan `docs/stories/` for `.md` files
2. Parse filenames in format `{epic}.{story}.{title}.md`
3. Create epic issues for each unique epic number
4. Create story issues from markdown content
5. Establish parent-child relationships
6. Generate a detailed migration log

**Example Structure:**
```
docs/stories/
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
  "story_count": 4,
  "log_file": "migration-log-20240124-143022.json",
  "story_dir": "/path/to/docs/stories"
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
      "type": "story",
      "file": "1.1.repository-setup.md",
      "issue_number": 16,
      "status": "created",
      "message": "Story migrated successfully",
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

# 2. Create stories for the epic (using new syntax)
STORY1_RESULT=$(./github-issue-manager.sh create-story "Database Schema Design" "
## Story
As a developer, I want a well-designed database schema so that data is properly organized and performant.

## Acceptance Criteria
- [ ] Entity relationship diagram created
- [ ] Primary and foreign keys defined
- [ ] Indexes planned for performance
- [ ] Migration scripts prepared
" "db-schema-design" --epic $EPIC_NUM "data-management")

STORY1_NUM=$(echo "$STORY1_RESULT" | jq -r '.story_number')
echo "Created Story #$STORY1_NUM"

# 3. Create tasks for the story (using new syntax)
./github-issue-manager.sh create-task "Create ER Diagram" "
Design entity relationship diagram showing all tables, relationships, and constraints.
" --story $STORY1_NUM "db-schema-design" --epic-slug "data-management"

./github-issue-manager.sh create-task "Write Migration Scripts" "
Create database migration scripts for initial schema setup.
" --story $STORY1_NUM "db-schema-design" --epic-slug "data-management"

# 4. Start working on the epic
./github-issue-manager.sh update-status $EPIC_NUM "In Progress"

echo "Epic workflow created successfully!"
```

### Standalone Stories and Tasks

```bash
#!/bin/bash

# Create a standalone story (not linked to any epic)
STORY_RESULT=$(./github-issue-manager.sh create-story "Fix Critical Bug" "
## Story
As a user, I want the critical bug fixed so that the application works correctly.

## Acceptance Criteria
- [ ] Bug is identified and analyzed
- [ ] Fix is implemented
- [ ] Tests are added to prevent regression
" "critical-bug-fix")

STORY_NUM=$(echo "$STORY_RESULT" | jq -r '.story_number')
echo "Created standalone story #$STORY_NUM"

# Create a standalone task (quick fix, no story or epic)
./github-issue-manager.sh create-task "Urgent hotfix" "
Apply emergency patch to production.
"

# Create a task with just epic label (cross-cutting concern)
./github-issue-manager.sh create-task "Update documentation" "
Update API documentation for all endpoints.
" --epic-slug "documentation"
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

# Move stories ready for review
REVIEW_STORIES=(16 21)

for story in "${REVIEW_STORIES[@]}"; do
    echo "Moving story #$story to Done..."
    ./github-issue-manager.sh update-status $story "Done"
done
```

### Story Creation from Template

```bash
#!/bin/bash

create_user_story() {
    local epic_num=$1
    local epic_slug=$2
    local feature_name=$3
    local story_slug=$4
    local user_type=$5
    local action=$6
    local benefit=$7
    
    local story_body="
## Story
As a $user_type, I want to $action so that $benefit.

## Acceptance Criteria
- [ ] Feature is accessible via UI
- [ ] Feature works correctly
- [ ] Feature has proper error handling
- [ ] Feature is tested
- [ ] Feature is documented

## Technical Notes
- Implement following BMAD standards
- Add appropriate unit tests
- Update API documentation
- Consider performance implications
"
    
    # Use new syntax with --epic flag
    ./github-issue-manager.sh create-story "$feature_name" "$story_body" "$story_slug" --epic $epic_num "$epic_slug"
}

# Create multiple related stories
EPIC_NUM=15
EPIC_SLUG="authentication"

create_user_story $EPIC_NUM "$EPIC_SLUG" "User Profile Management" "user-profile" "registered user" "manage my profile information" "I can keep my account details up to date"

create_user_story $EPIC_NUM "$EPIC_SLUG" "Password Change" "password-change" "registered user" "change my password" "I can maintain account security"

create_user_story $EPIC_NUM "$EPIC_SLUG" "Account Deletion" "account-deletion" "registered user" "delete my account" "I can remove my data when no longer needed"
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
- Creates GitHub Projects v2 board if it doesn't exist
- Links your repository to the project
- Uses default Status field with options: Todo, In Progress, Done
- Sets up proper field mapping for status transitions

### Labels

The script automatically creates and manages these labels:
- `epic` - Applied to all epic issues
- `story` - Applied to all story issues
- `task` - Applied to all task issues
- `epic:{epic_slug}` - Applied to epics and stories with specific epic slug
- `story:{story_slug}` - Applied to stories with specific story slug
- `story-{num}` - Applied to tasks belonging to specific story
- `migrated` - Applied to issues created via migration

## Troubleshooting

### Common Issues

#### "GitHub CLI not authenticated"
```bash
gh auth login
```

#### "core-config.yaml not found"
Ensure you have a `.bmad-core/core-config.yaml` file in your project root with proper GitHub configuration.

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
| `create-story-issue.sh` | `create-story` |
| `create-task-issue.sh` | `create-task` |
| `update-issue-status.sh` | `update-status` |
| `list-stories.sh` | `list-stories` |
| `migrate-md-to-issues.sh` | `migrate-stories` |

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