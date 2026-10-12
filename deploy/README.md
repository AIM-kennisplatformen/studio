# Deployment scripts

Scripts that deploy SCEPA to the staging and production VMs and check that they
are healthy. They deploy two repositories together: this one (Studio) and
[database-builder-scepa-rs](https://github.com/AIM-kennisplatformen/database-builder-scepa-rs)
(the upload stack, API and literature MCP).

| File | Purpose |
|---|---|
| `deploy.sh` | Deploys both stacks to one environment and writes a deployment record. |
| `deploy_smoke_test.sh` | Read-only health check of one environment. `deploy.sh` runs it after every deployment. |
| `environments.sh` | Host names, repositories and SSH helpers shared by both scripts. |
| `templates/Caddyfile.<env>` | The reverse-proxy config each VM should run. |

## Requirements

On your machine: bash 3.2 or newer (the macOS default works), `ssh`, `gh` (logged
in), `jq`, `git`, `curl` and `openssl`. On the VMs: passwordless `sudo`.

Set `SCEPA_SSH_USER` when your SSH login name differs from your local user name.
The scripts keep no user name of their own.

## Environments

| Environment | Host | Branch deployed from (both repositories) |
|---|---|---|
| `staging` | `kpscepastaging.mads-han.src.surf-hosted.nl` | `current-staging` |
| `production` | `scepakp.mads-han.src.surf-hosted.nl` | `current-production` |

## Deploy

```bash
export SCEPA_SSH_USER=<your login on the VMs>

deploy/deploy.sh staging                  # dry run: prints the plan, changes nothing
deploy/deploy.sh staging --apply          # deploy
deploy/deploy.sh production --apply       # asks you to type "production" first
```

Without `--apply` the script only reads. It resolves the exact commit for each
repository, compares it with what is live (through the GitHub compare API),
runs the preflight checks and diffs the Caddyfile. It stops, and exits 1, when a
check is marked `BLOCK`.

With `--apply` it, for each stack in turn: fetches and checks out the commit,
validates `compose.release.yaml`, runs `docker compose up -d --build --wait`,
and finally installs and reloads the Caddyfile only when it differs from the
template. It then waits for the local endpoints, runs `deploy_smoke_test.sh` and
writes the record. A second deployment cannot start while one is running (it
takes a lock on the VM).

Preflight checks that block a deployment:

- Docker or Caddy is not running, or less than 10 GiB is free for builds.
- A tracked file in a checkout on the VM is modified.
- The live commit is not on GitHub, or the target branch is behind or diverged
  from the live commit. Pass an explicit SHA to go back on purpose.
- A `.env` or `mcp_tools.local.json` is missing, or the studio `.env` belongs to
  another environment: `LANGFUSE_TRACING_ENVIRONMENT`, `OAUTH_REDIRECT_URI` and
  `FRONTEND_ORIGIN` must match the target host.
- The upload stack's commit changes while Restate still has invocations in
  flight. Drain them first, because workflow code changes are not safe with
  active invocations.

Options:

| Option | Effect |
|---|---|
| `--upload-ref REF`, `--studio-ref REF` | Deploy a branch name or a commit SHA (7 to 40 hex characters) instead of the environment's branch. A SHA is how you roll back. |
| `--reload-caddy` | Reload Caddy even when its config is unchanged. |
| `--no-smoke` | Skip the smoke test. |
| `--yes` | Skip the production confirmation prompt. |

Exit status is 0 on success, 1 when blocked or failed, 2 for bad usage.

## Smoke test

```bash
deploy/deploy_smoke_test.sh staging
deploy/deploy_smoke_test.sh production
```

It checks, without changing anything: public routes and the TLS certificate, the
Authentik login redirect, system services and disk space, every container and
healthcheck, local endpoints, the MCP token behaviour and tool list, the Qdrant
collection, Restate registration, the documents API, Studio's environment
(`LANGFUSE_TRACING_ENVIRONMENT`, OAuth callback, discovery URL), Studio's route
to the MCP server, and the git state of both checkouts. Secrets are read on the
VM and never leave it. Exit status is 1 when any check fails.

## Deployment records

Every `--apply` writes `deployment-records/<environment>-deploy-<UTC time>.md`
in the current directory, or in `SCEPA_DEPLOY_RECORDS` when set. A record has:

- the result, who ran it, when, and which script commit;
- both repositories: branch and commit before, requested ref, commit after, the
  relation to the live commit, and the commits and files that changed;
- software versions: OS and kernel; dpkg versions and the versions the programs
  report for Docker Engine, Compose, Buildx, containerd, runc, Caddy and Git;
  Docker and containerd configuration; what the image tags resolved to inside
  the containers (PostgreSQL, Redis, Qdrant, TypeDB, Restate, Garage, GROBID);
  image ids; system services; available package updates; volumes; and the
  live Caddyfile with its hash;
- a diff of package, runtime, image and configuration versions between before
  and after the deployment;
- the smoke test output and the deployment log;
- a rollback command that restores the previous commits.

Records hold host names, versions and commit ids but no secrets. This
repository is public and they describe the infrastructure, so keep them out of
it. `deployment-records/` is git-ignored here.

## Rolling back

The record ends with the exact command. For example:

```bash
deploy/deploy.sh production --apply --upload-ref <previous sha> --studio-ref <previous sha>
```

This restores code only. It does not undo data or schema changes in Postgres,
TypeDB, Qdrant, Garage or Restate, and it does not revert edits to the `.env`
files. After a SHA deployment the checkout on the VM is on a detached HEAD.

## Known limits

- The deployment is not atomic. A stack that fails to become healthy is left as
  it is, and the record says so. There is no automatic rollback.
- Caddy's config comes from `templates/`. Edit the template, not the file on the
  VM. The comparison is semantic (Caddy's adapted JSON), so whitespace
  differences do not trigger a reload.
- Docker and Caddy versions come from apt and are not pinned. `deploy.sh`
  records them but does not change them.
- A login to the VMs can fail for a moment while the VM rewrites
  `~/.ssh/authorized_keys`. The scripts open one shared connection, retrying
  that step, and reuse it for every later command.
