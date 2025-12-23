# Graphiti + LadybugDB Integration

Knowledge graph memory using Graphiti with LadybugDB backend for unified-mcp.

## Overview

This capability provides persistent knowledge graph storage with semantic search. It combines:
- **Graphiti**: Graph memory system with entity extraction and relationship mapping
- **LadybugDB**: Embedded graph database (Kuzu-compatible, no Docker required)

## Features

- **Automatic Entity Extraction**: Graphiti extracts entities and relationships from natural language
- **Semantic Search**: Vector similarity search across knowledge graph
- **Embedded Database**: No external database server needed (LadybugDB stores data locally)
- **Cypher Queries**: Full Cypher query language support for advanced graph traversal
- **Cross-Session Memory**: Knowledge persists across MCP server restarts

## Installation

### Requirements

- Python 3.12+ (required by Graphiti)
- OpenAI API key (for embeddings and LLM)

### Install Dependencies

```bash
pip install graphiti-core real_ladybug openai
```

### Environment Variables

Create a `.env` file or set environment variables:

```bash
export OPENAI_API_KEY=sk-...
```

## Usage

### Available Tools

#### 1. `store_insight`
Store a new insight or knowledge in the knowledge graph.

```json
{
  "content": "The unified-mcp project uses progressive discovery to reduce token usage by 96-160x",
  "source": "project documentation"
}
```

**Response:**
```json
{
  "status": "success",
  "tool": "store_insight",
  "message": "Insight stored successfully",
  "content": "..."
}
```

#### 2. `search_insights`
Search the knowledge graph using semantic search.

```json
{
  "query": "How does progressive discovery work?",
  "limit": 10
}
```

**Response:**
```json
{
  "status": "success",
  "tool": "search_insights",
  "query": "...",
  "results": {
    "nodes": [...],
    "edges": [...],
    "episodes": [...]
  },
  "count": {
    "nodes": 5,
    "edges": 3,
    "episodes": 2
  }
}
```

#### 3. `query_graph`
Execute custom Cypher query on the knowledge graph.

```json
{
  "cypher_query": "MATCH (e:Entity)-[r:RELATES_TO]->(m:Entity) RETURN e, r, m LIMIT 10",
  "params": {}
}
```

**Response:**
```json
{
  "status": "success",
  "tool": "query_graph",
  "query": "...",
  "results": [...],
  "count": 10
}
```

#### 4. `add_episode`
Add a conversational episode to the knowledge graph.

```json
{
  "name": "Implementation Discussion",
  "content": "We discussed implementing the Graphiti handler with LadybugDB backend.",
  "source_description": "team meeting"
}
```

**Response:**
```json
{
  "status": "success",
  "tool": "add_episode",
  "episode_uuid": "...",
  "name": "Implementation Discussion",
  "message": "Episode added successfully"
}
```

## Data Storage

### Database Location

The LadybugDB database is stored at:
```
capabilities/graphiti_ladybug/data/graphiti.db/
```

This directory contains the graph database files and is automatically created on first use.

### Schema

Graphiti uses a specific schema with node types:
- **Episodic**: Conversational episodes and events
- **Entity**: Extracted entities (people, places, concepts)
- **Community**: Entity communities/clusters
- **RelatesToNode_**: Relationship metadata

And relationship types:
- **RELATES_TO**: Entity-to-entity relationships with facts
- **MENTIONS**: Episode-to-entity mentions
- **HAS_MEMBER**: Community membership

## Architecture

### Custom LadybugDriver

We implement a custom `LadybugDriver` that adapts LadybugDB to Graphiti's GraphDriver interface:

```python
from handlers.knowledge_graph import LadybugDriver

driver = LadybugDriver(db_path="./data/graphiti.db")
```

The driver:
- Creates Graphiti schema in LadybugDB
- Translates Cypher queries to LadybugDB format
- Manages database connections and sessions

### GraphitiHandler

The handler integrates Graphiti with unified-mcp's progressive discovery:

```python
from handlers.knowledge_graph import GraphitiHandler

handler = GraphitiHandler(config)
await handler.initialize()
```

## Configuration

In `config/catalog.yaml`:

```yaml
knowledge_graph:
  enabled: true
  type: graphiti_ladybug
  source: capabilities/graphiti_ladybug
  tools:
    - store_insight
    - search_insights
    - query_graph
    - add_episode
  lazy_load: false  # Always available for cross-session memory
  description: "Knowledge graph memory using Graphiti + LadybugDB (embedded, no Docker)"
```

## Testing

Run integration tests:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all Graphiti tests
pytest tests/integration/test_graphiti_handler.py -v

# Skip slow tests (API calls)
pytest tests/integration/test_graphiti_handler.py -m "not slow"
```

**Note**: Tests require OpenAI API key to be set.

## Troubleshooting

### ImportError: No module named 'real_ladybug'

Install LadybugDB:
```bash
pip install real_ladybug
```

### ImportError: graphiti_core requires Python 3.12+

Upgrade to Python 3.12 or later:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### OpenAI API Error

Set your API key:
```bash
export OPENAI_API_KEY=sk-...
```

### Database Permission Error

Ensure the data directory is writable:
```bash
chmod -R 755 capabilities/graphiti_ladybug/data/
```

## Performance

- **Database**: LadybugDB is embedded (no network overhead)
- **Embeddings**: OpenAI API calls (cached by Graphiti)
- **Search**: Vector similarity + graph traversal (fast)
- **Storage**: Approximately 1MB per 1000 episodes (depends on content)

## License

This integration follows unified-mcp's license. Graphiti and LadybugDB have their own licenses:
- Graphiti: Apache 2.0
- LadybugDB: MIT

## References

- [Graphiti Documentation](https://github.com/zep-ai/graphiti)
- [LadybugDB Documentation](https://github.com/LadybugDB/ladybug)
- [Kuzu Cypher Documentation](https://docs.kuzudb.com/cypher/)
