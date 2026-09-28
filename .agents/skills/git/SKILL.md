---
name: git
description: Commit, pull, or push repository changes, and create or update a GitHub pull request. Use for Git commits, branch synchronization, pushes, and PR work.
---

# Git

Use the repository state and conversation history to describe the actual work. Follow repository-specific conventions when they exist, and keep unrelated changes out of the requested operation.

## Prerequisites

- Git is available and this repository has an `origin` remote.
- Run `gh` commands outside the sandbox from the start, requesting execution approval when needed. The sandbox may not expose keyring credentials and can report an invalid token for an authenticated account. Local Git inspection can run inside the sandbox.
- The `gh` CLI is installed and `gh auth status` succeeds for this repository before using this skill. If authentication fails, report the error and stop; do not silently skip GitHub context.
- Inspect the current branch and use `gh` to view its related issues before committing, pulling, pushing, or preparing a PR. Check the branch's PR links and issue numbers in its name or commits, then verify candidate issues with `gh issue view`. Do not infer an issue link from a loose text match alone.

Keep branch history linear: fast-forward or rebase when synchronizing; do not create merge commits. If asked to merge a PR, use a linear-history merge method supported by the repository.

- For a commit or commit message, read [references/commit.md](references/commit.md).
- For pulling or updating a branch, read [references/pull.md](references/pull.md).
- For pushing a branch, read [references/push.md](references/push.md).
- For a new pull request or an update to an existing PR, read [references/pr.md](references/pr.md).
- When a request combines operations, use the relevant references in workflow order. A push updates only the matching branch on `origin`; create or update a PR only when requested. Do not commit, push, or open a PR merely because a later workflow might need one.
