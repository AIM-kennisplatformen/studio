# Commit

## Goal

Create a commit that describes the staged change and its purpose, using the conversation and repository state for context.

## Workflow

1. Inspect `git status`, `git diff`, and `git diff --staged`. Stage only the intended changes, including relevant new files; check the staged diff for unrelated files, generated artifacts, logs, and secrets.
2. Check the current branch's related issues as directed by [SKILL.md](../SKILL.md). If the branch is linked to one or more issues, list their issue numbers in the commit description (the message body), for example `Related: #123`.
3. Follow documented repository commit conventions when present. Otherwise, use a concise imperative subject with a suitable type prefix when it helps. Add a body when context is needed. Explain the rationale for every breaking change or functional refactor in the body.
4. Include validation performed when it is relevant to understanding the change. Do not claim checks that were not run.
5. Before committing, confirm the final message matches the staged diff. Use a message file for multiline text so its line breaks are preserved. Do not add a Codex co-author trailer unless the user requests it.

## Output

Create a commit focused on the authorized changes and report its hash and any material validation limits.
