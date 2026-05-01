# qavajs — End-to-End Tests

## Docs
https://qavajs.github.io/

## Prerequisites

- [Node.js](https://nodejs.org/) (for npm/npx)
- [Pixi](https://pixi.sh/) (if using `pixi run qava_test`)
- [Docker & Docker Compose](https://docs.docker.com/get-docker/) (for containerised services)
- A valid `.env` file in the project root (see [Environment Setup](#environment-setup))

## Environment Setup

Copy the sample file and fill in the required secrets:

```bash
cp .env.sample .env
```

## Install Modules

From the `tests/bdd/` directory:

```bash
npm install
```

## Execute Tests

### Option 1: Full run (builds containers, runs tests, stops containers)

This is the recommended way to run tests from a clean state. It builds and starts all Docker containers (backend, MCP server, Authentik, Qdrant), waits for them to be ready, runs the tests, and stops everything afterwards.

```bash
pixi run qava_test
```

### Option 2: Tests only (containers/services already running)

If you already have the services running locally (e.g. via `docker compose up` or dev servers), you can run just the test directly from the `tests/bdd/` directory:

```bash
npx qavajs run --config config.mjs
```

Make sure the following services are reachable before running:

| Service | Default URL |
|---|---|
| Backend | `http://localhost:10090` |
| MCP Server | `http://localhost:8000` |
| LLM Worker | `http://localhost:9200` |
| Authentik | `http://localhost:9000` |

### Run a single feature file

```bash
npx qavajs run --config config.mjs -- features/chatbot.feature
```

## Test Data

Test credentials and URLs are configured in [memory/index.js](./memory/index.js). Defaults:

- Login URL: `http://localhost:10090/auth/login`
- Authentik user: `akadmin` / `admin`

## Project Structure
- [config.mjs](./config.mjs) — main qavajs/Cucumber config
- [features/](./features) — Gherkin test cases
- [memory/](./memory) — test data (URLs, credentials, messages)
- [page_object/](./page_object) — Playwright page object selectors
- [step_definition/](./step_definition) — custom step definitions
- [report/](./report) — HTML test reports (generated after a run)
