---
name: github-board-manager
description: >
  Executes GitHub project board operations for the github-issues-generator skill.
  Handles CRUD operations for GitHub issues with type classification (epic, sub-epic, feature, task).
  Supports filtering/retrieval by issue type, parent-child linking, and project board status updates.
  Use when you need to (1) create issues with a specific type, (2) retrieve issues filtered by type,
  (3) link issues to parent issues, (4) update issue status on project boards.
  Triggers: "post this epic", "retrieve all features", "link to parent", "update status", "list epics",
  "create an epic", "create a sub-epic", "add a user feature", "move issue to In Progress", "list issues".
---

# GitHub Board Manager

Manage GitHub issues with hierarchical relationships (Epic → Sub-Epic → Feature → Task) and project board integration using the `github-issue-manager.sh` script.

## When to Use

- Creating GitHub issues with type classification (epic, sub-epic, feature, task)
- Retrieving existing issues filtered by type for context-gathering
- Linking child issues to parent issues (e.g., feature → epic)
- Updating issue status on the project board
- Querying issues by type, status, or parent

## When NOT to Use

- **Content generation**: Use `github-issues-generator` skill for drafting issue content
- **Issue templates or hierarchy decisions**: Handled by `github-issues-generator`
- **Improving/expanding descriptions**: Delegate to `github-issues-generator`

## Prerequisites

Before using, ensure `.roo/skills/core-config.yaml` exists in the project root:

```yaml
github:
  repo: "owner/repo-name"
  project_board: "Project Board Name"
```

## GitHub Issue Types

This skill operates on 4 issue types that must be specified when creating or retrieving issues:

| Type | Parent Allowed | Children Allowed | Type Flag |
|------|----------------|------------------|-----------|
| `epic` | None | sub-epic, feature | `--issue-type epic` |
| `sub-epic` | epic | feature | `--issue-type sub-epic` |
| `feature` | epic, sub-epic | task | `--issue-type feature` |
| `task` | feature | None | `--issue-type task` |

## Quick Reference

| Command | Syntax | Returns |
|---------|--------|---------|
| Create Epic | `create-epic <title> <body> <slug>` | `{"epic_number": N}` |
| Create Sub-Epic | `create-sub-epic <title> <body> <slug> --parent <num> <slug>` | `{"sub_epic_number": N, "parent_epic_number": N}` |
| Create Feature | `create-feature <title> <body> <slug> --parent <num> <slug>` | `{"feature_number": N, "parent_number": N}` |
| Create Task | `create-task <title> <body> --parent <num> <slug>` | `{"task_number": N, "parent_feature_number": N}` |
| List by Type | `list-issues --issue-type <type>` | `[{issue}, ...]` |
| List by Parent | `list-issues --parent <num>` | `[{issue}, ...]` |
| Get Context | `get-issue-context <num>` | `{issue with hierarchy}` |
| Update Status | `update-status <num> <status>` | `{"updated": true}` |

Run script at: `scripts/github-issue-manager.sh` (relative to this skill directory)

## Slug Creation Rules

Slugs are **required** for epics, sub-epics, and features. Create them by:
- Deriving from title, lowercase
- Replace spaces with hyphens
- Alphanumeric and hyphens only
- Max 20 characters
- Use abbreviations (e.g., "auth" for "authentication")
- Omit stop words ("the", "and", "of")

**Never use issue numbers as slugs** - the script validates this.

Examples: `user-auth`, `db-schema`, `ci-pipeline`, `login-flow`

## Workflows

### Workflow 1: Create Epic

**Input:** Title, body, slug  
**Output:** `{"epic_number": N}`

```bash
./github-issue-manager.sh create-epic "User Authentication" "Implement full auth system" "user-auth"
# Returns: {"epic_number": 15}
```

Epics get:
- GitHub issue type `Epic`
- Added to project board with status `Epic Structure`

### Workflow 2: Create Sub-Epic

**Input:** Title, body, slug, parent epic number, parent epic slug  
**Output:** `{"sub_epic_number": N, "parent_epic_number": N}`

```bash
./github-issue-manager.sh create-sub-epic "Database Layer" "Database infrastructure and data model setup" "db-layer" --parent 15 "user-auth"
# Returns: {"sub_epic_number": 20, "parent_epic_number": 15}
```

Sub-epics get:
- GitHub issue type `sub-epic`
- Sub-issue relationship to parent epic
- Added to project board with status `Epic Structure`

### Workflow 3: Create Feature

**Input:** Title, body, slug, parent (epic or sub-epic) number, parent slug  
**Output:** `{"feature_number": N, "parent_number": N}`

```bash
./github-issue-manager.sh create-feature "Password Reset" "As a user, I want to reset my password..." "password-reset" --parent 15 "user-auth"
# Returns: {"feature_number": 25, "parent_number": 15}
```

Features get:
- GitHub issue type `Feature`
- Sub-issue relationship to parent epic or sub-epic
- Added to project board with status `Backlog`

### Workflow 4: Create Task

**Input:** Title, body, parent feature number, parent feature slug  
**Output:** `{"task_number": N, "parent_feature_number": N}`

```bash
./github-issue-manager.sh create-task "Implement token refresh" "Add JWT refresh logic..." --parent 25 "password-reset"
# Returns: {"task_number": 30, "parent_feature_number": 25}
```

Tasks get:
- GitHub issue type `Feature`
- Sub-issue relationship to parent feature
- Added to project board with status `Backlog`

### Workflow 5: Retrieve Issues

**Input:** Filter criteria (issue type, status, parent, search term, or issue number)  
**Output:** JSON array of matching issues or single issue context

#### By Issue Type

```bash
# List all epics
./github-issue-manager.sh list-issues --issue-type epic

# List all sub-epics
./github-issue-manager.sh list-issues --issue-type sub-epic

# List all features
./github-issue-manager.sh list-issues --issue-type feature

# List all tasks
./github-issue-manager.sh list-issues --issue-type task

```

#### By Parent

```bash
# List features under epic #15
./github-issue-manager.sh list-issues --parent 15

# List tasks under feature #25
./github-issue-manager.sh list-issues --parent 25
```

#### Get Full Context (with hierarchy)

```bash
./github-issue-manager.sh get-issue-context 16
# Returns: {"number": 16, "type": "feature", "title": "...", "body": "...", "parent": {...}, "children": [...]}
```

#### Search by Keyword

```bash
./github-issue-manager.sh list-issues --search "authentication"
```

### Workflow 6: Update Status

**Input:** Issue number, status  
**Output:** `{"updated": true}`

Valid statuses: `Backlog`, `Ready`, `In Progress`, `AI Review`, `Review`, `Done`

```bash
./github-issue-manager.sh update-status 16 "In Progress"
# Returns: {"updated": true}
```