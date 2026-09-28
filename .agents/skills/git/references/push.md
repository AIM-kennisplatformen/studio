# Push

## Goal

Push the current local branch to the branch with the same name on `origin`. A push request alone does not create or update a pull request.

## Workflow

1. Check the branch's related issues as directed by [SKILL.md](../SKILL.md). Confirm the current branch is named (not detached), `origin` points to the intended repository, and the working tree and outgoing commits match the request.
2. Run the checks documented by this repository for the changed files, if any. Do not invent a build or test command when none is configured.
3. Fetch `origin` and inspect `origin/<current-branch>` if it exists. If it has commits missing locally, follow [pull.md](pull.md) to fast-forward or rebase before pushing. Check the outgoing history for merge commits and resolve any before pushing.
4. Push `HEAD` explicitly to the matching remote branch, setting upstream tracking when needed: `branch=$(git branch --show-current)` followed by `git push -u origin "HEAD:refs/heads/$branch"`. For example, local `feat/agent-skills` must push to `origin/feat/agent-skills`.
5. If a published branch was rebased, use the remote tip recorded before the rebase. If a normal push is rejected because the remote still has the old commits, verify that tip has not changed and use `--force-with-lease=refs/heads/<current-branch>:<recorded-tip>` for that same branch. If the remote has changed, synchronize again instead. Never use plain `--force`.
6. If the push fails for authentication, permissions, or branch rules, report the exact error. Do not rewrite remotes or switch protocols as a workaround. If the user also requested a PR, follow [pr.md](pr.md) after the push.

## Output

Report the pushed branch and validation performed. If a PR was requested, include its URL.
