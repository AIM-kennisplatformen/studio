---
name: github-board-manager
description: This skill ties in to the github-issues-generator skill in this repository. Where this skill handles the different GitHub project board tasks, the github-issues-generator is responsible for the generation of the content. But, both work in harmony, tying in into each others workflows.

This skill handles the execution of GitHub project board tasks such as creating new issues, improving existing issues and retreiving exisiting issues to use as context for generation in the github-issue-generator skill in this repository. There are four different kinds of GitHub issue types that this skill needs to be able to handle. Epics, sub-epics, features, and tasks.

Use when user wants to (1) create epics, sub-epics, features, or tasks as GitHub issues. (2) link issues to other issues as sub-issues, (3) create sub-epics linked to parent epics, (4) update issue status on project boards, (5) list or query issues, (6) get context for a specific feature, (7) migrate markdown files to GitHub issues. Triggers on phrases like "create an epic", "create a sub-epic", "add a user feature", "move issue to In Progress", "list issues", "create a task for".
---


# GitHub Projects Skill

Manage GitHub issues with hierarchical relationships (Epic → Sub-Epic → issue → Task) and project board integration using the `github-issue-manager.sh` script.

## Prerequisites

Before using, ensure `.roo/skills/core-config.yaml` exists in the project root:

```yaml
github:
  repo: "owner/repo-name"
  project_board: "Project Board Name"
```

<!-- Required labels (`epic`, `issue`, `task`) are auto-created on first use. -->

## Quick Reference

| Command | Syntax |
|---------|--------|
| Create Epic | `create-epic <title> <body> <epic_slug>` |
| Create Sub-Epic | `create-sub-epic <title> <body> <sub_epic_slug> --parent <num> <parent_slug>` |
| Create issue | `create-issue <title> <body> <issue_slug> [--epic <num> <epic_slug>]` |
| Create Task | `create-task <title> <body> [--issue <num> <issue_slug>] [--epic-slug <slug>]` |
| Update Status | `update-status <issue_num> <status>` |
| List issues | `list-issues [filter]` |
| Get Context | `get-issue-context <issue_num>` |

Run script at: `.roo/skills/github-projects/scripts/github-issue-manager.sh`

## Slug Creation Rules

Slugs are **required** for epics and issues. Create them by:
- Deriving from title, lowercase
- Replace spaces with hyphens
- Alphanumeric and hyphens only
- Max 20 characters
- Use abbreviations (e.g., "auth" for "authentication")
- Omit stop words ("the", "and", "of")

**Never use issue numbers as slugs** - the script validates this.

Examples: `user-auth`, `db-schema`, `ci-pipeline`, `login-flow`

## Workflows
### Workflow 1: Create epic

```bash
# 1. Create epic
./github-issue-manager.sh create-epic "User Authentication" "Implement full auth system" "user-auth"
# Returns: {"epic_number": 15}
```

## Workflow 2: Create sub-epic

```bash
# Create a sub-epic linked to parent epic #15
./github-issue-manager.sh create-sub-epic "Database Layer" "Database infrastructure and data model setup" "db-layer" --parent 15 "user-auth"
# Returns: {"sub_epic_number": 20, "parent_epic_number": 15}

# issues can link to the sub-epic using its slug
./github-issue-manager.sh create-feature "Schema Design" "Design the database schema..." "schema-design" --epic 20 "db-layer"
```

Sub-epics get:
- Both their own `epic:sub-slug` label and parent's `epic:parent-slug` label
- Sub-issue relationship to parent epic
- Added to project board

## Workflow 3: Create feature

```bash
# 1. Create issue (linked to epic or sub-epic)
./github-issue-manager.sh create-feature "Password Reset" "As a user, I want to reset my password..." "password-reset" --epic 15 "user-auth" --issue_type "feature"
# Returns: {"issue_number": 15}
```

## Workflow 4: Create Task

## Workflow 5: Retrieve issues


```bash
# List issues
./github-issue-manager.sh list-issues "type:issue"

# List epics
./github-issue-manager.sh list-issues "type:epic"

# Get full context for a issue
./github-issue-manager.sh get-issue-context 16
```

### Update Status

Valid statuses: `Backlog`, `Ready`, `In Progress`, `AI Review`, `Review`, `Done`

```bash
./github-issue-manager.sh update-status 16 "In Progress"
```

### Query Stories

