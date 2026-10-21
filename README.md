# Studio

A React frontend and FastAPI backend for chat-based knowledge graph exploration.
The browser reaches the backend through the frontend's same-origin
`/chatep/api` proxy.
The backend never builds or serves frontend assets.

## Project structure

```text
backend/                 # Python/Pixi project, tests, and backend Dockerfile
  src/                   # FastAPI package and application code
  tests/                 # Backend pytest suite
  scripts/               # Backend support scripts
frontend/                # React/npm project and frontend Dockerfile
compose.yaml             # Development containers
compose.release.yaml     # Release target overrides
```

Pixi manages only the backend. The frontend uses npm directly or its Node
container.

## Environment

Copy `.env.sample` to `.env` and supply the OAuth, LLM, and other service
credentials needed by your environment.

The default OAuth redirect URI is
`http://localhost:10090/chatep/api/auth/callback`. The frontend's
`/chatep/api` proxy forwards that callback to the backend; the backend does not
serve frontend assets.

The default MCP configuration in `backend/mcp_tools.json` uses the production
MCP server at `https://scepakp.mads-han.src.surf-hosted.nl/mcp`. Studio does not
require Scepa's Docker network or a local Scepa MCP deployment.

The production MCP requires a bearer token. Keep that token out of Git by
copying the configuration to the ignored `backend/mcp_tools.local.json`, setting
its `auth` value to the production `MCP_BEARER_TOKEN`, and selecting it in
`.env`:

```dotenv
MCP_TOOL_CONFIG_PATH=mcp_tools.local.json
```

The release Compose configuration mounts this ignored file read-only at
`/app/mcp_tools.local.json`; it is excluded from the Docker build context and
is not stored in the release image. The local file should contain:

```json
{
  "mcpServers": {
    "scepa-literature": {
      "url": "https://scepakp.mads-han.src.surf-hosted.nl/mcp",
      "auth": "REPLACE_WITH_PRODUCTION_MCP_BEARER_TOKEN"
    }
  }
}
```

Default published ports are deliberately distinct from Scepa:

| Service | URL or host port |
|---|---|
| Frontend and proxied API | `http://localhost:10090/chatep/` |
| Backend (direct) | `http://localhost:10092/api` |
| Redis | `6379` |
| PostgreSQL | `5433` |

## Docker development

Start the Vite frontend, reload-enabled backend, Redis, and PostgreSQL:

```bash
docker compose up --build
```

Vite serves the application at `http://localhost:10090/chatep/` and proxies
`/chatep/api`, including Socket.IO, to the backend. Source directories are bind-mounted, while
`/app/node_modules` and `/app/.pixi` are anonymous volumes so host dependencies
are never copied into the containers.

## Docker release

Build the backend release target and the Nginx frontend target:

```bash
docker compose -f compose.release.yaml up --build
```

Nginx serves the SPA under `/chatep/` and proxies `/chatep/api` to the backend
container.

### Release networking and administrative access

The release Compose configuration builds the backend and frontend `release`
stages and binds every published port to `127.0.0.1`. This keeps the services
reachable from the deployment host without exposing them through the VM's
public network interfaces.

The frontend loopback port is intended as the upstream for a reverse proxy such
as Caddy, which should provide public HTTPS on ports 80 and 443. The direct
backend, Redis, and PostgreSQL ports are for administration and diagnostics;
do not change them to `0.0.0.0`. Access them remotely through SSH tunnels.

| Service | Release endpoint on the VM |
|---|---|
| Frontend and proxied API | `http://127.0.0.1:10090/chatep/` |
| Backend, for direct diagnostics | `http://127.0.0.1:10092/api` |
| Redis | `127.0.0.1:6379` |
| PostgreSQL | `127.0.0.1:5433` |

For example, forward PostgreSQL to port `5433` on an administrator workstation:

```bash
ssh -N -L 5433:127.0.0.1:5433 user@your-vm
```

Multiple services can be forwarded in one SSH session:

```bash
ssh -N \
  -L 10092:127.0.0.1:10092 \
  -L 6379:127.0.0.1:6379 \
  -L 5433:127.0.0.1:5433 \
  user@your-vm
```

Keep the SSH session open while using the forwarded services. Replace
`user@your-vm` with the deployment account and VM hostname. If a local port is
already occupied, change only the first port in its rule; for example,
`-L 15433:127.0.0.1:5433` exposes PostgreSQL locally on port `15433`.

Port variables in `.env` change both the VM loopback port and the corresponding
SSH-tunnel source port. Inspect the effective release configuration before
deployment with:

```bash
docker compose -f compose.release.yaml config
```

### Single-host HTTPS routing

Studio uses `/chatep/` as its base path in development and release builds. A
production deployment at `scepakp.mads-han.src.surf-hosted.nl` must set:

```dotenv
BACKEND_BASE_URL=https://scepakp.mads-han.src.surf-hosted.nl/chatep/api
FRONTEND_BASE_URL=https://scepakp.mads-han.src.surf-hosted.nl/chatep/
FRONTEND_ORIGIN=https://scepakp.mads-han.src.surf-hosted.nl
OAUTH_REDIRECT_URI=https://scepakp.mads-han.src.surf-hosted.nl/chatep/api/auth/callback
```

Register that exact HTTPS callback URL with the OAuth provider. The release
Nginx container accepts `/chatep/` directly, so Caddy must preserve rather than
strip the prefix:

```caddy
scepakp.mads-han.src.surf-hosted.nl {
    encode zstd gzip

    handle /mcp* {
        reverse_proxy 127.0.0.1:8002 {
            flush_interval -1
        }
    }

    redir /upload /upload/ 308

    handle /upload/* {
        basic_auth {
            operator REPLACE_WITH_CADDY_PASSWORD_HASH
        }

        reverse_proxy 127.0.0.1:5173
    }

    redir /chatep /chatep/ 308

    handle /chatep/* {
        reverse_proxy 127.0.0.1:10090
    }

    handle {
        respond "Not found" 404
    }
}
```

## Backend development

Run backend tooling from the backend Pixi project:

```bash
cd backend
pixi run test
pixi run lint
pixi run typecheck
```

The optional Authentik setup helper is also backend-owned:

```bash
python backend/scripts/setup_authentik.py
```

It reads the repository `.env` and expects an Authentik container named
`authentik-server`. `AUTHENTIK_BASE_URL` can override its default local URL,
`http://localhost:10091`.

## Frontend development

For a host-native frontend workflow:

```bash
cd frontend
npm ci
npm run dev
```

Frontend checks run with `npm run check`.
