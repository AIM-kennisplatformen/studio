# Knowledge Graph API Backend

FastAPI backend for chat-based knowledge graph generation and node context retrieval.

## Dependencies

This project depends on data files in the `../knowledge-graph/` directory:
- `example-data.json` - Contains entities (nuggets) and relationships
- `QnA-questions.json` - Contains questions with associated entities and relations

The backend loads these files on startup to populate the knowledge graph.

## Setup

This project uses `uv` for Python dependency management. Dependencies are defined in `pyproject.toml`.

### Prerequisites

- Python 3.14 (specified in `.python-version`)
- `uv` package manager ([installation guide](https://github.com/astral-sh/uv))

### Install Dependencies

```bash
cd test-backend
uv sync
```

This will:
- Create a virtual environment in `.venv/`
- Install all dependencies specified in `pyproject.toml`
- Lock dependency versions in `uv.lock`

## Running the Server

### Development Mode (with auto-reload)

```bash
uv run fastapi dev app/main.py
```

Or alternatively:

```bash
uv run uvicorn app.main:app --reload
```

The server will start at: `http://localhost:8000`

### Production Mode

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### 1. POST `/chats/{chatId}/messages`

Send a message to a chat session and receive a knowledge graph response based on a randomly selected question from the knowledge base.

**Important:** The request body message is currently ignored. The endpoint selects a random question and returns its answer along with the associated knowledge graph nodes and edges.

#### Request

```bash
curl -X POST http://localhost:8000/chats/test-chat/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "any message"}'
```

**Request Body:**
```json
{
  "message": "string (currently ignored)"
}
```

#### Successful Response (200 OK)

```json
{
  "message": "[[Sophie Blake|5]] plays the [[bass|33]] guitar, as documented in [[relationship 45|45]], which identifies it as her primary instrument.\n\n## Bassist Profile\n\nBlake was born in Seattle, Washington in 1991...",
  "nodes": [
    {
      "id": "5",
      "type": "musician",
      "label": "Sophie Blake",
      "attributes": {
        "description": "Bass guitarist and composer, former member of Stellar Drift",
        "birth_year": 1991,
        "birth_place": "Seattle, Washington",
        "active_years": "2012-present"
      }
    },
    {
      "id": "33",
      "type": "instrument",
      "label": "Bass",
      "attributes": {
        "description": "Low-frequency stringed instrument bridging rhythm and harmony",
        "category": null,
        "origin_region": "United States",
        "first_appeared": "1950s",
        "range": "E1-G4 (standard tuning)",
        "difficulty": "intermediate"
      }
    }
  ],
  "edges": [
    {
      "id": "45",
      "sourceId": "5",
      "targetId": "33",
      "labelToSource": "played by",
      "labelToTarget": "plays",
      "type": "relation",
      "attributes": {
        "description": "Primary instrument"
      }
    }
  ],
  "sources": [],
  "error": null
}
```

**Response Fields:**
- `message` (string): The answer to the randomly selected question, formatted in markdown with wiki-links
- `nodes` (array): Entity nodes from the knowledge graph referenced in the question
  - `id` (string): Unique identifier
  - `type` (string): Entity type (musician, band, song, genre, instrument)
  - `label` (string): Display name
  - `attributes` (object): All entity-specific data
- `edges` (array): Relationships between nodes
  - `id` (string): Unique identifier
  - `sourceId` (string): Source node ID
  - `targetId` (string): Target node ID
  - `labelToTarget` (string): Relationship label from source to target
  - `labelToSource` (string): Relationship label from target to source
  - `type` (string): Always "relation"
  - `attributes` (object): Relationship metadata
- `sources` (array): Always empty in current implementation
- `error` (string|null): Error message if request failed, null on success

#### Error Response (500)

```json
{
  "message": "",
  "nodes": [],
  "edges": [],
  "sources": [],
  "error": "Knowledge graph data not loaded"
}
```

**Error Scenarios:**
- Knowledge graph data files not found or failed to load
- Invalid JSON in data files
- No questions available in the database

### 2. GET `/nodes/{nodeId}/context`

Get contextual information for a specific node in the knowledge graph.

**Note:** Currently not implemented. Returns empty data with error message.

#### Request

```bash
curl http://localhost:8000/nodes/123/context
```

#### Response (200 OK)

```json
{
  "message": "",
  "nodes": [],
  "edges": [],
  "sources": [],
  "error": "Not implemented yet"
}
```

### 3. GET `/`

Health check endpoint showing API status and loaded data statistics.

#### Request

```bash
curl http://localhost:8000/
```

#### Successful Response (200 OK)

```json
{
  "status": "ok",
  "message": "Knowledge Graph API is running",
  "version": "0.1.0",
  "data": {
    "entities_count": 34,
    "relations_count": 53,
    "questions_count": 100
  }
}
```

#### Error Response (if data not loaded)

```json
{
  "status": "error",
  "message": "Knowledge graph data not loaded",
  "version": "0.1.0"
}
```

## Interactive API Documentation

Once the server is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs (try out API calls directly)
- **ReDoc**: http://localhost:8000/redoc (clean documentation view)
- **OpenAPI JSON**: http://localhost:8000/openapi.json (raw API specification)

## Project Structure

```
test-backend/
├── .venv/                # Virtual environment (created by uv sync)
├── app/
│   ├── __init__.py       # Package initialization
│   ├── main.py           # FastAPI application and endpoints
│   ├── models.py         # Pydantic models for request/response
│   └── data_loader.py    # Knowledge graph data loading utilities
├── .python-version       # Python version specification (3.14)
├── pyproject.toml        # Project dependencies and metadata
├── uv.lock               # Locked dependency versions
└── README.md             # This file
```

## Data Files (in ../knowledge-graph/)

```
knowledge-graph/
├── example-data.json     # Entities and relationships
├── QnA-questions.json    # Question-answer pairs with entity/relation references
└── schema.md             # Knowledge graph schema documentation
```

## Data Models

### ChatResponse
```python
{
  "message": str,           # Answer text with markdown/wiki-links
  "nodes": List[Node],      # Knowledge graph entities
  "edges": List[Edge],      # Relationships between entities
  "sources": List[Source],  # Currently always empty
  "error": str | null       # Error message or null
}
```

### Node
```python
{
  "id": str,                # Unique entity identifier
  "type": str,              # Entity type (musician, band, song, etc.)
  "label": str,             # Display name
  "attributes": dict        # Entity-specific attributes
}
```

### Edge
```python
{
  "id": str,                # Unique relationship identifier
  "sourceId": str,          # Source entity ID
  "targetId": str,          # Target entity ID
  "labelToTarget": str,     # Relationship label (source → target)
  "labelToSource": str,     # Relationship label (target → source)
  "type": str,              # Always "relation"
  "attributes": dict        # Relationship metadata
}
```

### Source
```python
{
  "title": str,             # Source title
  "type": str,              # Source type (e.g., "url")
  "infoUrl": str | null,    # URL to source
  "snippet": str | null     # Excerpt from source
}
```

## Testing Examples

### Test the health endpoint
```bash
curl http://localhost:8000/
```

### Get a random Q&A response
```bash
curl -X POST http://localhost:8000/chats/my-chat/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### Check response summary
```bash
curl -s -X POST http://localhost:8000/chats/test/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' | \
python3 -c "import sys, json; data=json.load(sys.stdin); \
print(f'Nodes: {len(data[\"nodes\"])}, Edges: {len(data[\"edges\"])}, Error: {data[\"error\"]}')"
```

## Development

### Adding New Endpoints

1. Define Pydantic models in `app/models.py`
2. Add endpoint handlers in `app/main.py`
3. Test using the interactive docs at http://localhost:8000/docs

### CORS Configuration

The API currently allows all origins for development. For production, update CORS settings in `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict to your domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Modifying Knowledge Graph Data

Edit the source files in `../knowledge-graph/`:
- `example-data.json` - Add/modify entities and relationships
- `QnA-questions.json` - Add/modify questions and answers

Restart the server to reload the data.

## Implementation Notes

- The `/chats/{chatId}/messages` endpoint currently **ignores the input message** and returns a random question/answer
- Questions reference entities and relations by ID from the knowledge graph
- Nodes and edges are automatically populated from these ID references
- The `sources` field is intentionally left empty in the current implementation
- Wiki-link syntax `[[text|id]]` is used in answers to reference entities

## TODO

- [ ] Implement actual chat logic (use input message instead of random selection)
- [ ] Implement context retrieval for `/nodes/{nodeId}/context` endpoint
- [ ] Add support for filtering questions by topic/entity
- [ ] Add database integration for persistence
- [ ] Add authentication/authorization
- [ ] Add rate limiting
- [ ] Add comprehensive logging
- [ ] Add unit and integration tests
- [ ] Add caching for frequently accessed questions