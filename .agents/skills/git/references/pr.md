# Pull request

## Goal

Create or update a pull request whose title, description, and scope match the branch's actual changes. Give reviewers the problem, resulting behavior, and validation performed.

## Workflow

1. Read the conversation for the intended outcome and constraints. Check the branch's related issues as directed by [SKILL.md](../SKILL.md), repository contribution guidance, and a PR template if one exists.
2. Inspect the current branch, its upstream, `git status`, and the diff and commit list against the intended base branch. Determine the base from the user's instructions or repository defaults; do not assume the branch is based on `main`.
3. Check for an existing PR for this branch before creating one. If one exists, update it when that matches the request rather than opening a duplicate.
4. Account for uncommitted changes: they cannot appear in a PR. If the request includes committing them, use [commit.md](commit.md) first. Otherwise, describe only what is on the branch and flag relevant changes that remain local.
5. Write a concise, specific title that follows any documented repository convention. Lead the description with the concrete problem and resulting behavior. Summarize changes, rationale, meaningful trade-offs, and checks actually run, including failures or relevant checks not run. Follow any PR template and required fields; remove unsupported claims and placeholders.
6. Review the final comparison for unrelated commits, generated files, secrets, and accidental changes. Resolve problems within the authorized scope or report them. Use draft status when requested or when the branch is intentionally awaiting work or review; do not mark it ready solely to satisfy a workflow.
7. When needed, push the branch using [push.md](push.md). Create or edit the PR with `gh pr create` or `gh pr edit`, passing multiline descriptions as a file or structured tool argument. Preserve existing PR metadata and discussion unless a change was requested. Verify the URL, title, base and head branches, description, and status.

## Output

Give the user the PR URL and any material validation limits.
