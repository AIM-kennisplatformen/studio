# Pull and update a branch

## Goal

Synchronize the current branch without creating merge commits.

## Workflow

1. Check the branch's related issues as directed by [SKILL.md](../SKILL.md). Confirm the current branch and `origin`. Inspect `git status`; preserve uncommitted work before rebasing. Do not commit or stash unrelated changes without accounting for them.
2. Run `git fetch origin` and record the current `origin/<current-branch>` tip before any rebase. If that remote branch exists, fast-forward to it when possible. If local and remote have diverged, rebase local commits onto `origin/<current-branch>`. If the remote branch does not exist, leave the local branch intact.
3. Rebase onto `origin/main` only when the user asks to update the feature branch from main. Fetch first and confirm `origin/main` exists. This may rewrite published commits; [push.md](push.md) governs any subsequent force-with-lease push.
4. If a rebase conflicts, inspect both versions and their intent with `git status`, `git diff`, and the relevant files. Resolve each conflict, stage it, and run `git rebase --continue`. Use `git rebase --abort` if the intended resolution cannot be determined safely. During a rebase, inspect content before choosing `ours` or `theirs` because their meanings can be counterintuitive.
5. Verify that the branch contains the intended changes, has no merge commits in its outgoing history, and passes the repository's documented checks when available. Do not push unless pushing was also requested.

## Output

Report what was synchronized, any conflicts resolved, validation performed, and whether publishing rewritten commits will require force-with-lease.
