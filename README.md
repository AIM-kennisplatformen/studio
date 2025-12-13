# **Studio App**

This repository contains a complete custom Studio application composed of:

* **Frontend** — `src/frontend`
* **MCP Server** — `src/mcp_servers`
* **Backend API** — `src/backend`
* **LLM Worker** — `src/llm_worker`

All components run locally within a **Pixi environment**.
No LibreChat or Docker-based workflow is required for development.

---

# 🚀 Features

* Modular architecture with isolated components
* Custom MCP server with optional Zotero + Qdrant vector search
* Pluggable LLM worker (Ollama or OpenAI-compatible providers such as Nebius)
* Fully custom frontend build pipeline
* Optional OAuth (Authentik)
* Optional telemetry (Langfuse)

---

# 🖥️ System Requirements

## Development Requirements

* Linux, macOS, or Windows
* Intel/AMD x86_64 or ARM 64-bit
* **Pixi** installed → [https://pixi.sh/latest/installation/](https://pixi.sh/latest/installation/)
* No GPU required unless running local inference

## Optional — GPU Local Inference

If you plan to run large models locally via Ollama:

* NVIDIA GPU ≥ 12GB VRAM recommended
* CUDA-compatible drivers
* Ollama installed

---

# 📁 Project Structure

```
src/
  frontend/        # Custom UI
  mcp_servers/     # MCP server implementation
  backend/         # Backend API orchestrator
  llm_worker/      # LLM inference worker
```

---

# 🔧 Configuration Files

Two configuration files must be created before the system can run:

### 1. `.env`

```
cp .env.sample .env
```

### 2. `llm_worker_config.toml`

```
cp llm_worker_config.sample.toml llm_worker_config.toml
```

Both must be fully configured before starting the system.

---

# 📑 Environment Variables (`.env`)

Below is the full explanation of every field included in `.env.sample`.

---

## 📚 Zotero (Optional — MCP Paper Search)

Used only if the MCP server needs to query academic papers.

```
ZOTERO_API_KEY=""
ZOTERO_LIBRARY_ID=""
ZOTERO_COLLECTION_ID=""
```

### Where to find them:

* **API key** → Zotero settings → Feeds/API
* **Library ID** → URL:
  `https://www.zotero.org/groups/<library_id>/<name>/library`
* **Collection ID** → URL:
  `https://.../collections/<collection_id>/collection`

Leave blank if not using Zotero.

---

## 🗂️ Qdrant Vector Database

Used for document embeddings / semantic search.

```
QDRANT_URL="http://127.0.0.1"
QDRANT_PORT=6333
```

Defaults are correct for local Qdrant.

---

## 🌐 Backend URL

This URL is used internally by the frontend and MCP server to reach the backend.

```
BACKEND_BASE_URL=http://127.0.0.1:8090
```

---

## 🤖 LLM Worker URL

The backend sends inference jobs to the worker.

```
LLM_WORKER_URL=http://127.0.0.1:8002
```

Match this to your worker port.

---

## 🔐 Optional — Authentik OAuth Login

If your frontend uses OAuth:

```
OAUTH_CLIENT_ID=
OAUTH_CLIENT_SECRET=
OAUTH_DISCOVERY_URL=https://<authentik_url>/application/o/<app_name>/.well-known/openid-configuration
```

Leave unused if not using OAuth.

---

## 📊 Optional — Langfuse Telemetry

If you want tracing / prompt analytics:

```
LANGFUSE_SECRET_KEY=""
LANGFUSE_PUBLIC_KEY=""
LANGFUSE_HOST=""
```

---

## ✔️ Minimal Working `.env` Example

For a simple local dev environment:

```dotenv
QDRANT_URL="http://127.0.0.1"
QDRANT_PORT=6333

BACKEND_BASE_URL=http://127.0.0.1:8090
LLM_WORKER_URL=http://127.0.0.1:8002
```

---

# ⚙️ LLM Worker Configuration (`llm_worker_config.toml`)

This config controls the LLM provider and model used by the worker.

---

## **Default: Local Ollama Setup**

```toml
[llm]
client_type = "ollama"
model_type = "qwen2.5:7b"
max_tokens = 1000
host = "http://localhost:11434/v1"
api_key = "ollama"
mcp_server = "http://localhost:8000/sse"
```

### Requirements:

```
ollama serve
ollama pull qwen2.5:7b
```

---

## **Alternative: OpenAI-Compatible Provider (Nebius, OpenAI, Groq, etc.)**

```toml
[llm]
client_type = "ollama"
model_type = "Qwen/Qwen3-32b"
host = "https://api.studio.nebius.ai/v1"
api_key = "<YOUR-NEBIUS-API-KEY>"
max_tokens = 1000
mcp_server = "http://localhost:8000/sse"
```

Change these for your provider:

* `client_type = "openai"`
* `model_type` → provider model name
* `host` → provider’s API endpoint
* `api_key` → provider API key

---

# 🏗️ Development Workflow

**Run all commands inside a Pixi shell:**

```
pixi shell
```

Then follow this order:

---

## **1. Build the Frontend**

```
pixi run frontend_build
```

Compiles frontend assets.

---

## **2. Start the MCP Server**

```
pixi run mcp_server
```

This must start before the worker and backend.

---

## **3. Start the LLM Worker**

```
pixi run llm_worker
```

Handles inference and communicates with the MCP server.

---

## **4. Start the Backend**

```
pixi run backend_no_docker
```

This is the API core that coordinates all components.

---

# 🔄 Startup Summary

| Order | Component               | Command                      |
| ----- | ----------------------- | ---------------------------- |
| 1     | **Frontend Build**      | `pixi run frontend_build`    |
| 2     | **MCP Server**          | `pixi run mcp_server`        |
| 3     | **LLM Worker**          | `pixi run llm_worker`        |
| 4     | **Backend (No Docker)** | `pixi run backend_no_docker` |

---

# 🧪 First-Run Checklist

Before running everything:

✔ `.env` created and filled
✔ `llm_worker_config.toml` filled
✔ Qdrant running (optional)
✔ Ollama running if using local inference
✔ MCP server reachable
✔ Ports not in use

---

# ❓ Troubleshooting

### Worker cannot connect to MCP Server

Check:

* `mcp_server` URL in `llm_worker_config.toml`
* MCP is running before worker

### Backend cannot reach worker

Check:

* `LLM_WORKER_URL` in `.env`

### Frontend calls fail

Check:

* `BACKEND_BASE_URL` in `.env`

---
