# Studio

A chat-based knowledge graph application. A React frontend communicates over Socket.IO with a FastAPI backend. The backend uses an LLM agent (via `mcp-use`) backed by an MCP server that queries Qdrant and Zotero for literature-supported answers.

> **Note:** The MCP server (`src/mcp_servers/`) will be moved to a separate repository in the future.

---

## Project Structure

```
src/
  backend/          # FastAPI app (Python)
    endpoints/      # auth, chat, graph, log_event, assets
    utility/        # chat_util, graph_data_loader, graph_api_models
    config.py       # env config + prompt templates
    main.py         # app entry point
  frontend/         # React + Vite app
    src/
scripts/            # setup_authentik.py, run_qava_test.py
tests/
  bdd/              # qavajs end-to-end tests
docker-compose.yml
pyproject.toml
```

---

## Prerequisites

- [Pixi](https://pixi.sh/) — manages the Python + Node environment
- [Docker & Docker Compose](https://docs.docker.com/get-docker/) — for containerised deployment
- A running [Qdrant](https://qdrant.tech/) instance
- A running [Authentik](https://goauthentik.io/) instance (OAuth2 provider)
- A running LLM endpoint (OpenAI-compatible, e.g. Ollama or a hosted model)
- A [Zotero](https://www.zotero.org/) library + API key

---

## Environment Setup

Copy the sample env file and fill in the required values:

```bash
cp .env.sample .env
```

Key variables:

| Variable | Description |
|---|---|
| `BACKEND_BASE_URL` | Public URL of the backend, e.g. `http://localhost:10090` |
| `OAUTH_DISCOVERY_URL` | Authentik OIDC discovery URL |
| `OAUTH_CLIENT_ID` | Authentik OAuth2 client ID |
| `OAUTH_CLIENT_SECRET` | Authentik OAuth2 client secret |
| `SESSION_SECRET` | Secret key for session cookies |
| `LLM_MODEL` | Model name, e.g. `gpt-4o` or an Ollama model |
| `OPENAI_HOST` | Base URL of your OpenAI-compatible LLM endpoint |
| `MCP_TOOL_CONFIG_PATH` | Path to the MCP tool config JSON file |
| `QDRANT_URL` | Qdrant host |
| `QDRANT_PORT` | Qdrant port (default `6333`) |
| `ZOTERO_API_KEY` | Zotero API key |
| `ZOTERO_LIBRARY_ID` | Zotero library ID |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key (observability) |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key |
| `LANGFUSE_HOST` | Langfuse host URL |
| `PG_PASS` | PostgreSQL password (only when spinning your own authentik and not using the deployed authentik) |
| `AUTHENTIK_SECRET_KEY` | Authentik secret key (only when spinning your own authentik and not using the deployed authentik) |

---

## Running With Docker

Start the application through Docker Compose:

```bash
pixi run application
```

This starts:
- `application` — builds the Vite frontend into `kg/` and runs the FastAPI app on port `10090`
- `redis` — runs Redis on port `6379`

The application serves the built frontend from `kg/` and exposes the API at `http://localhost:10090`.

### Frontend HMR

To start the Vite dev server and switch `/app` to it while it is running:

```bash
pixi run frontend_hmr
```

This starts Vite at `http://localhost:5173`. While it is running, `http://localhost:10090/app` stays on the backend URL and proxies frontend files from Vite; when it stops, the application serves the built frontend from `kg/` again.

### Direct Docker Commands

Build the image once:

```bash
docker build -t studio_application -f dockerfiles/Dockerfile .
```

Then start all services:

```bash
docker compose up
```

---

## Authentik Setup

Authentik is used as the OAuth2/OIDC provider. To set up the OAuth2 application automatically:

```bash
python scripts/setup_authentik.py
```

This requires a running Authentik instance and reads credentials from `.env`.

---

## Testing

End-to-end tests are written with [qavajs](https://qavajs.github.io/) (Cucumber + Playwright).

### Run all tests (spins up containers automatically)

```bash
python scripts/run_qava_test.py
```

### Run tests against already-running services

From `tests/bdd/`:

```bash
npm install
npx qavajs run --config config.mjs
```

Services must be reachable at:

| Service | Default URL |
|---|---|
| Backend | `http://localhost:10090` |
| MCP Server | `http://localhost:8000` |
| Authentik | `http://localhost:9000` |

### Run a single feature

```bash
npx qavajs run --config config.mjs -- features/chatbot.feature
```

---

## Code Quality

```bash
pixi run ruff check
pixi run mypy .
```
