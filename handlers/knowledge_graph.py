"""
Graphiti + LadybugDB Handler
==============================

Knowledge graph memory via Graphiti with LadybugDB backend.

Maps unified-mcp tools to Graphiti operations:
- store_insight → add_episode (store new knowledge)
- search_insights → search (semantic search)
- query_graph → custom Cypher query
- add_episode → add_episode (add conversational episode)

LadybugDB provides embedded graph database (no Docker required).
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from graphiti_core import Graphiti
from graphiti_core.driver.driver import GraphDriver, GraphDriverSession, GraphProvider
from graphiti_core.llm_client import OpenAIClient
from graphiti_core.embedder import OpenAIEmbedder
from graphiti_core.nodes import EpisodeType

from core.capability_loader import CapabilityHandler

# LadybugDB imports
try:
    import real_ladybug as lb
except ImportError:
    raise ImportError(
        "real_ladybug is required for GraphitiHandler. "
        "Install it with: pip install real_ladybug"
    )


class LadybugDriverSession(GraphDriverSession):
    """LadybugDB driver session for Graphiti."""

    provider = GraphProvider.KUZU  # LadybugDB uses Kuzu-compatible API

    def __init__(self, driver: "LadybugDriver"):
        self.driver = driver

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def close(self):
        pass

    async def execute_write(self, func, *args, **kwargs):
        return await func(self, *args, **kwargs)

    async def run(self, query: str, **kwargs: Any) -> Any:
        """Execute Cypher query on LadybugDB."""
        params = {k: v for k, v in kwargs.items() if v is not None}
        # Remove Neo4j-specific parameters
        params.pop("database_", None)
        params.pop("routing_", None)

        try:
            result = self.driver.conn.execute(query, params)
            # Convert LadybugDB result to list of dicts
            records = []
            while result.has_next():
                records.append(result.get_next())
            return records
        except Exception as e:
            logging.error(f"LadybugDB query error: {e}\n{query}\n{params}")
            raise


class LadybugDriver(GraphDriver):
    """LadybugDB driver for Graphiti."""

    provider: GraphProvider = GraphProvider.KUZU
    aoss_client: None = None

    def __init__(self, db_path: str = ":memory:"):
        """Initialize LadybugDB driver.

        Args:
            db_path: Path to LadybugDB database directory (default: in-memory)
        """
        super().__init__()
        self.db = lb.Database(db_path)
        self.conn = lb.Connection(self.db)
        self.setup_schema()

    def setup_schema(self):
        """Create Graphiti schema in LadybugDB."""
        # LadybugDB uses same schema as Kuzu
        schema_queries = """
            CREATE NODE TABLE IF NOT EXISTS Episodic (
                uuid STRING PRIMARY KEY,
                name STRING,
                group_id STRING,
                created_at TIMESTAMP,
                source STRING,
                source_description STRING,
                content STRING,
                valid_at TIMESTAMP,
                entity_edges STRING[]
            );
            CREATE NODE TABLE IF NOT EXISTS Entity (
                uuid STRING PRIMARY KEY,
                name STRING,
                group_id STRING,
                labels STRING[],
                created_at TIMESTAMP,
                name_embedding FLOAT[],
                summary STRING,
                attributes STRING
            );
            CREATE NODE TABLE IF NOT EXISTS Community (
                uuid STRING PRIMARY KEY,
                name STRING,
                group_id STRING,
                created_at TIMESTAMP,
                name_embedding FLOAT[],
                summary STRING
            );
            CREATE NODE TABLE IF NOT EXISTS RelatesToNode_ (
                uuid STRING PRIMARY KEY,
                group_id STRING,
                created_at TIMESTAMP,
                name STRING,
                fact STRING,
                fact_embedding FLOAT[],
                episodes STRING[],
                expired_at TIMESTAMP,
                valid_at TIMESTAMP,
                invalid_at TIMESTAMP,
                attributes STRING
            );
            CREATE REL TABLE IF NOT EXISTS RELATES_TO(
                FROM Entity TO RelatesToNode_,
                FROM RelatesToNode_ TO Entity
            );
            CREATE REL TABLE IF NOT EXISTS MENTIONS(
                FROM Episodic TO Entity,
                uuid STRING PRIMARY KEY,
                group_id STRING,
                created_at TIMESTAMP
            );
            CREATE REL TABLE IF NOT EXISTS HAS_MEMBER(
                FROM Community TO Entity,
                FROM Community TO Community,
                uuid STRING,
                group_id STRING,
                created_at TIMESTAMP
            );
        """

        for query in schema_queries.split(";"):
            query = query.strip()
            if query:
                self.conn.execute(query)

    async def execute_query(
        self, cypher_query: str, **kwargs: Any
    ) -> tuple[list[dict[str, Any]] | list[list[dict[str, Any]]], None, None]:
        """Execute Cypher query."""
        params = {k: v for k, v in kwargs.items() if v is not None}
        params.pop("database_", None)
        params.pop("routing_", None)

        try:
            result = self.conn.execute(cypher_query, params)
            records = []
            while result.has_next():
                records.append(result.get_next())
            return records, None, None
        except Exception as e:
            params_preview = {k: (v[:5] if isinstance(v, list) else v) for k, v in params.items()}
            logging.error(f"LadybugDB query error: {e}\n{cypher_query}\n{params_preview}")
            raise

    def session(self, _database: str | None = None) -> GraphDriverSession:
        """Create a new session."""
        return LadybugDriverSession(self)

    async def close(self):
        """Close database connection."""
        pass

    def delete_all_indexes(self, database_: str):
        """Delete all indexes (no-op for LadybugDB)."""
        pass

    async def build_indices_and_constraints(self, delete_existing: bool = False):
        """Build indices (no-op for LadybugDB - schema-based)."""
        pass


class GraphitiHandler(CapabilityHandler):
    """Handler for Graphiti knowledge graph tools with LadybugDB backend."""

    def __init__(self, config: dict):
        """Initialize handler with config."""
        super().__init__(config)
        self.db_path: Optional[str] = None
        self.graphiti: Optional[Graphiti] = None

    async def initialize(self) -> None:
        """Initialize Graphiti with LadybugDB."""
        # Get database path from config (default to ~/.unified-mcp/graphiti)
        source = self.config.get("source", "capabilities/graphiti_ladybug")
        self.db_path = str(Path(source) / "data" / "graphiti.db")

        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Initializing Graphiti with LadybugDB at: {self.db_path}")

        # Create LadybugDB driver
        driver = LadybugDriver(db_path=self.db_path)

        # Initialize Graphiti with LadybugDB
        # Note: Requires OpenAI API key in environment
        self.graphiti = Graphiti(
            graph_driver=driver,
            llm_client=OpenAIClient(),
            embedder=OpenAIEmbedder(),
        )

        self.logger.info("Graphiti + LadybugDB initialized successfully")

    async def get_tool_schema(self, tool_name: str) -> dict:
        """Get JSON schema for a tool."""
        schemas = {
            "store_insight": {
                "name": "store_insight",
                "description": (
                    "Store a new insight or knowledge in the knowledge graph. "
                    "Creates entities and relationships from natural language."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The insight or knowledge to store",
                        },
                        "source": {
                            "type": "string",
                            "description": "Source description (e.g., 'user conversation', 'documentation')",
                            "default": "user input",
                        },
                    },
                    "required": ["content"],
                },
            },
            "search_insights": {
                "name": "search_insights",
                "description": (
                    "Search the knowledge graph using semantic search. "
                    "Returns relevant entities, relationships, and episodes."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (natural language)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
            },
            "query_graph": {
                "name": "query_graph",
                "description": (
                    "Execute a custom Cypher query on the knowledge graph. "
                    "For advanced graph traversal and pattern matching."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "cypher_query": {
                            "type": "string",
                            "description": "Cypher query to execute",
                        },
                        "params": {
                            "type": "object",
                            "description": "Query parameters",
                            "default": {},
                        },
                    },
                    "required": ["cypher_query"],
                },
            },
            "add_episode": {
                "name": "add_episode",
                "description": (
                    "Add a conversational episode to the knowledge graph. "
                    "Extracts entities and relationships automatically."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Episode name/title",
                        },
                        "content": {
                            "type": "string",
                            "description": "Episode content (conversation, event, etc.)",
                        },
                        "source_description": {
                            "type": "string",
                            "description": "Description of the source",
                            "default": "user conversation",
                        },
                    },
                    "required": ["name", "content"],
                },
            },
        }

        if tool_name not in schemas:
            raise ValueError(f"Unknown tool: {tool_name}")

        return schemas[tool_name]

    async def execute(self, tool_name: str, arguments: dict) -> dict:
        """Execute a Graphiti tool."""
        if tool_name == "store_insight":
            return await self._store_insight(arguments)
        elif tool_name == "search_insights":
            return await self._search_insights(arguments)
        elif tool_name == "query_graph":
            return await self._query_graph(arguments)
        elif tool_name == "add_episode":
            return await self._add_episode(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _store_insight(self, args: dict) -> dict:
        """Store insight as an episode in knowledge graph."""
        content = args["content"]
        source = args.get("source", "user input")

        try:
            # Store as episode (Graphiti extracts entities/relationships)
            await self.graphiti.add_episode(
                name=f"Insight: {content[:50]}...",
                episode_body=content,
                source_description=source,
                reference_time=datetime.now(),
                source=EpisodeType.message,
            )

            return {
                "status": "success",
                "tool": "store_insight",
                "message": "Insight stored successfully",
                "content": content,
            }

        except Exception as e:
            self.logger.error(f"Error storing insight: {e}")
            raise RuntimeError(f"Graphiti error: {e}")

    async def _search_insights(self, args: dict) -> dict:
        """Search knowledge graph semantically."""
        query = args["query"]
        limit = args.get("limit", 10)

        try:
            # Use Graphiti's search functionality
            results = await self.graphiti.search(query, num_results=limit)

            # Format results
            formatted_results = {
                "nodes": [
                    {
                        "uuid": node.uuid,
                        "name": node.name,
                        "summary": getattr(node, "summary", None),
                        "type": type(node).__name__,
                    }
                    for node in results.nodes
                ],
                "edges": [
                    {
                        "uuid": edge.uuid,
                        "fact": edge.fact,
                        "source": edge.source_node_uuid,
                        "target": edge.target_node_uuid,
                    }
                    for edge in results.edges
                ],
                "episodes": [
                    {
                        "uuid": ep.uuid,
                        "name": ep.name,
                        "content": ep.content,
                        "valid_at": str(ep.valid_at),
                    }
                    for ep in results.episodes
                ],
            }

            return {
                "status": "success",
                "tool": "search_insights",
                "query": query,
                "results": formatted_results,
                "count": {
                    "nodes": len(results.nodes),
                    "edges": len(results.edges),
                    "episodes": len(results.episodes),
                },
            }

        except Exception as e:
            self.logger.error(f"Error searching insights: {e}")
            raise RuntimeError(f"Graphiti search error: {e}")

    async def _query_graph(self, args: dict) -> dict:
        """Execute custom Cypher query."""
        cypher_query = args["cypher_query"]
        params = args.get("params", {})

        try:
            # Execute query via driver
            driver_session = self.graphiti.driver.session()
            records = await driver_session.run(cypher_query, **params)

            return {
                "status": "success",
                "tool": "query_graph",
                "query": cypher_query,
                "results": records,
                "count": len(records),
            }

        except Exception as e:
            self.logger.error(f"Error executing Cypher query: {e}")
            raise RuntimeError(f"Cypher query error: {e}")

    async def _add_episode(self, args: dict) -> dict:
        """Add conversational episode to knowledge graph."""
        name = args["name"]
        content = args["content"]
        source_description = args.get("source_description", "user conversation")

        try:
            # Add episode with Graphiti
            episode_uuid = await self.graphiti.add_episode(
                name=name,
                episode_body=content,
                source_description=source_description,
                reference_time=datetime.now(),
                source=EpisodeType.message,
            )

            return {
                "status": "success",
                "tool": "add_episode",
                "episode_uuid": episode_uuid,
                "name": name,
                "message": "Episode added successfully",
            }

        except Exception as e:
            self.logger.error(f"Error adding episode: {e}")
            raise RuntimeError(f"Graphiti error: {e}")

    async def cleanup(self) -> None:
        """Cleanup Graphiti and LadybugDB resources."""
        if self.graphiti:
            await self.graphiti.close()
            self.logger.info("Graphiti + LadybugDB closed")
