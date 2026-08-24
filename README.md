# Studio

A React frontend and FastAPI backend for chat-based knowledge graph exploration.
The browser reaches the backend through the frontend's same-origin `/api` proxy.
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

The default OAuth redirect URI remains
`http://localhost:10090/auth/callback` for compatibility with the hosted
Authentik provider. The frontend proxies that callback to the backend; the
backend does not serve frontend assets.

The default MCP configuration in `backend/mcp_tools.json` uses the production
MCP server over HTTPS. Studio does not require Scepa's Docker network or a local
Scepa MCP deployment. Set `MCP_TOOL_CONFIG_PATH` to use another configuration.

Default published ports are deliberately distinct from Scepa:

| Service | URL or host port |
|---|---|
| Frontend and proxied API | `http://localhost:10090` |
| Backend (direct) | `http://localhost:10092/api` |
| Redis | `6379` |
| PostgreSQL | `5433` |

## Docker development

Start the Vite frontend, reload-enabled backend, Redis, and PostgreSQL:

```bash
docker compose up --build
```

Vite serves the application at `http://localhost:10090` and proxies `/api`,
including Socket.IO, to the backend. Source directories are bind-mounted, while
`/app/node_modules` and `/app/.pixi` are anonymous volumes so host dependencies
are never copied into the containers.

## Docker release

Build the backend release target and the Nginx frontend target:

```bash
docker compose -f compose.release.yaml up --build
```

Nginx serves the SPA and proxies `/api` to the backend container.

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
