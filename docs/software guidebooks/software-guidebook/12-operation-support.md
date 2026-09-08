# 12. Operation and Support

This chapter provides information for operating, monitoring, and troubleshooting the Studio application in production.

## 12.1 Monitoring

### 12.1.1 Available Monitoring

| Component | Monitoring | Access |
|-----------|------------|--------|
| LLM Calls | Langfuse traces | Langfuse dashboard |
| Qdrant | Built-in dashboard | `http://localhost:6333/dashboard` |
| Backend | Console logs | Docker logs / stdout |
| Frontend | Browser console | Developer tools |

### 12.1.2 Langfuse Integration

Langfuse provides observability for LLM operations:

**Traced Operations**:
- LLM chat completions
- MCP tool invocations
- Token usage

**Configuration**:
```dotenv
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Access**: Log in to Langfuse dashboard to view traces.

### 12.1.3 Qdrant Dashboard

Qdrant provides a built-in web dashboard:

**URL**: `http://localhost:6333/dashboard`

**Available Information**:
- Collection statistics
- Vector counts
- Search testing interface

### 12.1.4 TODO: Recommended Additional Monitoring

| Component | Recommendation | Purpose |
|-----------|----------------|---------|
| Backend | Add Prometheus metrics | Request latency, error rates |
| Frontend | Add error boundary + reporting | Client-side errors |
| All services | Structured logging (JSON) | Log aggregation |
| Infrastructure | Container health checks | Automatic restart |

## 12.2 Health Checks

### 12.2.1 Manual Health Checks

| Service | Check | Expected |
|---------|-------|----------|
| Backend | `curl http://localhost:10090/docs` | OpenAPI docs page |
| Frontend | `curl http://localhost:10090/app` | HTML response |
| MCP Server | `curl http://localhost:8000/` | SSE endpoint |
| Qdrant | `curl http://localhost:6333/` | JSON status |
| LLM Worker | `curl http://localhost:9200/` | FastAPI response |

### 12.2.2 Docker Health Check Example

Add to `docker-compose.yml`:

```yaml
services:
  kg-backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:10090/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 12.3 Logging

### 12.3.1 Current Logging

| Service | Logger | Output |
|---------|--------|--------|
| Backend | print statements | stdout |
| LLM Worker | loguru | stderr |
| MCP Server | print + loguru | stdout/stderr |

### 12.3.2 Log Locations (Docker)

```bash
# View logs for specific service
docker compose logs kg-backend
docker compose logs llm-worker
docker compose logs mcp-server

# Follow logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100
```

### 12.3.3 Important Log Messages

| Message | Meaning | Action |
|---------|---------|--------|
| `✓ Socket connected` | User connected via WebSocket | Normal |
| `❌ Rejecting socket: no user in session` | Unauthenticated connection | Check OAuth config |
| `[PREFETCH ERROR - ...]` | Background prefetch failed | Check LLM Worker status |
| `Starting worker on http://...` | LLM Worker starting | Normal |

## 12.4 Troubleshooting

### 12.4.1 Common Issues

#### Backend Cannot Reach LLM Worker

**Symptoms**:
- Chat messages return "worker unavailable"
- 500 errors in backend logs

**Diagnosis**:
```bash
# Check if worker is running
curl http://localhost:9200/docs

# Check worker logs
docker compose logs llm-worker
```

**Solutions**:
1. Ensure LLM Worker is started
2. Verify `LLM_WORKER_URL` and `LLM_WORKER_PORT` in `.env`
3. Check network connectivity between containers

#### MCP Server Connection Failed

**Symptoms**:
- LLM responses don't cite literature
- Tool call errors in Langfuse

**Diagnosis**:
```bash
# Check if MCP server is running
curl http://localhost:8000/

# Check MCP server logs
docker compose logs mcp-server
```

**Solutions**:
1. Start MCP Server before LLM Worker
2. Verify `mcp_server` URL in `llm_worker_config.toml`
3. Check Qdrant connectivity

#### OAuth Redirect Loop

**Symptoms**:
- User redirected to login repeatedly
- Cannot access `/app`

**Diagnosis**:
- Check browser cookies
- Verify OAuth callback URL

**Solutions**:
1. Clear browser cookies
2. Ensure `BACKEND_BASE_URL` matches actual URL
3. Verify Authentik application settings

#### No Literature in Responses

**Symptoms**:
- AI answers but doesn't cite sources
- "No relevant literature found" messages

**Diagnosis**:
```bash
# Check Qdrant collection
curl http://localhost:6333/collections/knowledgeplatform

# Check Zotero credentials
# (look for auth errors in mcp-server logs)
```

**Solutions**:
1. Verify Qdrant collection is populated
2. Check `ZOTERO_API_KEY`, `ZOTERO_LIBRARY_ID` in `.env`
3. Ensure papers have matching tags in Zotero

### 12.4.2 Debug Mode

For detailed debugging, modify logging levels:

**Backend**:
```python
# Add to main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**LLM Worker** (already uses loguru):
```python
# src/llm_worker/main.py
logger.add(sys.stderr, level="DEBUG")
```

## 12.5 Runbooks

### 12.5.1 Restart All Services

```bash
# Stop all services
docker compose down

# Start all services
docker compose up -d

# Verify all services are running
docker compose ps
```

### 12.5.2 Update Deployment

```bash
# Pull latest changes
git pull

# Rebuild images
docker compose build

# Restart with new images
docker compose up -d
```

### 12.5.3 Clear User Sessions

Currently, sessions are in-memory. To clear all sessions:

```bash
# Restart the backend
docker compose restart kg-backend
```

### 12.5.4 Backup Qdrant Data

```bash
# Create snapshot
curl -X POST http://localhost:6333/collections/knowledgeplatform/snapshots

# List snapshots
curl http://localhost:6333/collections/knowledgeplatform/snapshots
```

### 12.5.5 View LLM Traces

1. Open Langfuse dashboard
2. Navigate to Traces
3. Filter by date range or user
4. Click trace for detailed view

## 12.6 Performance Tuning

### 12.6.1 LLM Worker

| Setting | Location | Impact |
|---------|----------|--------|
| `max_tokens` | `llm_worker_config.toml` | Response length limit |
| `max_steps` | `ask.py:54` | Agent iteration limit |
| Timeout | httpx client | Request timeout |

### 12.6.2 Qdrant

| Setting | Location | Impact |
|---------|----------|--------|
| `limit` | `qdrant_source.py` | Number of results |
| Collection config | Qdrant | Index parameters |

### 12.6.3 Backend

| Setting | Location | Impact |
|---------|----------|--------|
| Uvicorn workers | CLI argument | Concurrent requests |
| CORS origins | `main.py` | Allowed origins |

## 12.7 Security Operations

### 12.7.1 Rotate Session Secret

1. Generate new secret:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Update `SESSION_SECRET` in `.env`
3. Restart backend (all sessions will be invalidated)

### 12.7.2 Rotate OAuth Credentials

1. Generate new credentials in Authentik
2. Update `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` in `.env`
3. Restart backend

### 12.7.3 Review Access Logs

Currently, access logging is limited. Consider adding:
- Request logging middleware
- Authentication event logging
- Rate limiting

## 12.8 Known Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| No persistent sessions | Lost on restart | Accept for dev/demo use |
| No automatic session cleanup | Memory growth | Periodic restarts |
| Single Qdrant collection | One domain only | Manual collection switching |
| No metrics export | Limited observability | Use Langfuse for LLM ops |
