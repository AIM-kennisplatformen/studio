---
name: github-projects
description: Manage GitHub issues as epics, sub-epics, stories, and tasks with project board integration. Use when user wants to (1) create epics, sub-epics, user stories, or tasks as GitHub issues, (2) link stories to epics or tasks to stories as sub-issues, (3) create sub-epics linked to parent epics, (4) update issue status on project boards, (5) list or query stories, (6) get context for a specific story, (7) migrate markdown files to GitHub issues. Triggers on phrases like "create an epic", "create a sub-epic", "add a user story", "move issue to In Progress", "list stories", "create a task for".
---

# GitHub Projects Skill

Manage GitHub issues with hierarchical relationships (Epic → Sub-Epic → Story → Task) and project board integration using the `github-issue-manager.sh` script.

## Prerequisites

Before using, ensure `.bmad-core/core-config.yaml` exists in the project root:

```yaml
github:
  repo: "owner/repo-name"
  project_board: "Project Board Name"
```

Required labels (`epic`, `story`, `task`) are auto-created on first use.

## Quick Reference

| Command | Syntax |
|---------|--------|
| Create Epic | `create-epic <title> <body> <epic_slug>` |
| Create Sub-Epic | `create-sub-epic <title> <body> <sub_epic_slug> --parent <num> <parent_slug>` |
| Create Story | `create-story <title> <body> <story_slug> [--epic <num> <epic_slug>]` |
| Create Task | `create-task <title> <body> [--story <num> <story_slug>] [--epic-slug <slug>]` |
| Update Status | `update-status <issue_num> <status>` |
| List Stories | `list-stories [filter]` |
| Get Context | `get-story-context <issue_num>` |

Run script at: `.roo/skills/github-projects/scripts/github-issue-manager.sh`

## Slug Creation Rules

Slugs are **required** for epics and stories. Create them by:
- Deriving from title, lowercase
- Replace spaces with hyphens
- Alphanumeric and hyphens only
- Max 20 characters
- Use abbreviations (e.g., "auth" for "authentication")
- Omit stop words ("the", "and", "of")

**Never use issue numbers as slugs** - the script validates this.

Examples: `user-auth`, `db-schema`, `ci-pipeline`, `login-flow`

## Workflows

### Create a new Epic

Ask the user for a title and a description to use for the new epic. Then check if the projectboard contains existing epic, features or user stories that relate or overlap with the intent of the new epic. If so, show the user a list of matching issues. Also, ask the user if they want to provide reference to issues that should relate to the new epic.
Then, improve the given description, based on the provided context, and make it more detailed and systematic. Write the new description into a markdown file in a top-level folder called "issue-drafts". Present the improved description to the user and give them the following options:
* Accept new description and create epic on storyboard.
* Accept new description then stop. Do not create an issue on the projectoard (yet).
* The user gets to provide instructions and corrections. Use this input to further improve the new description, and repeat asking the user for next steps.

After the epic has been approved, generate a list of candidate user stories. Only the user story sentence/title.

```bash
# 1. Create epic
./github-issue-manager.sh create-epic "User Authentication" "Implement full auth system" "user-auth"
# Returns: {"epic_number": 15}

# 2. Create linked story
./github-issue-manager.sh create-story "User Login" "As a user, I want to login..." "user-login" --epic 15 "user-auth"
```

### Create Sub-Epic

Sub-epics are epics that are children of a parent epic. Use for breaking down large epics into smaller, related epics.

```bash
# Create a sub-epic linked to parent epic #15
./github-issue-manager.sh create-sub-epic "Database Layer" "Database infrastructure and data model setup" "db-layer" --parent 15 "user-auth"
# Returns: {"sub_epic_number": 20, "parent_epic_number": 15}

# Stories can link to the sub-epic using its slug
./github-issue-manager.sh create-story "Schema Design" "Design the database schema..." "schema-design" --epic 20 "db-layer"
```

Sub-epics get:
- Both their own `epic:sub-slug` label and parent's `epic:parent-slug` label
- Sub-issue relationship to parent epic
- Added to project board

### Create Story with Tasks

```bash
# 1. Create story (standalone or linked to epic)
./github-issue-manager.sh create-story "Password Reset" "As a user, I want to reset my password..." "password-reset" --epic 15 "user-auth"
# Returns: {"story_number": 16}

# 2. Create linked task
./github-issue-manager.sh create-task "Create reset form UI" "Implement the password reset form..." --story 16 "password-reset"
```

### Update Status

Valid statuses: `Backlog`, `Ready`, `In Progress`, `AI Review`, `Review`, `Done`

```bash
./github-issue-manager.sh update-status 16 "In Progress"
```

### Query Stories

```bash
# List open stories
./github-issue-manager.sh list-stories "label:story state:open"

# List epics
./github-issue-manager.sh list-stories "label:epic state:open"

# Get full context for a story
./github-issue-manager.sh get-story-context 16
```

## User Story Format

When creating stories, use this body structure:

```markdown
## Story
As a [role], I want to [action] so that [benefit].

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Tasks
- Task 1
- Task 2
```

## Advanced Reference

For complete documentation including migration workflows, bulk operations, and troubleshooting, see: [references/github-issue-manager-reference.md](references/github-issue-manager-reference.md)
