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

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from graphiti_core import Graphiti
from graphiti_core.driver.driver import GraphDriver, GraphDriverSession, GraphProvider
from graphiti_core.embedder import OpenAIEmbedder
from graphiti_core.llm_client import OpenAIClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.nodes import EpisodeType

from core.capability_loader import CapabilityHandler

# Optional imports for alternative providers
try:
    from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
    from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
    from graphiti_core.llm_client.gemini_client import GeminiClient

    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from graphiti_core.llm_client.anthropic_client import AnthropicClient

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

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
        # Don't filter None values - LadybugDB needs all referenced parameters
        params = dict(kwargs)
        # Remove Neo4j-specific parameters
        params.pop("database_", None)
        params.pop("routing_", None)

        try:
            result = self.driver.conn.execute(query, params)
            # Convert LadybugDB result to list of dicts
            # Get column names from the result
            column_names = result.get_column_names()
            records = []
            while result.has_next():
                row = result.get_next()
                # Convert row list to dict using column names
                record_dict = {col: row[i] for i, col in enumerate(column_names)}
                records.append(record_dict)
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

        # Install and load FTS extension for full-text search
        try:
            self.conn.execute("INSTALL FTS")
            self.conn.execute("LOAD EXTENSION FTS")
        except Exception as e:
            # Extension might already be installed/loaded
            logging.debug(f"FTS extension setup: {e}")

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

        # Create FTS indexes for full-text search using CALL syntax
        try:
            # Entity table FTS index
            self.conn.execute(
                """
                CALL CREATE_FTS_INDEX('Entity', 'node_name_and_summary', ['name', 'summary'])
            """
            )
        except Exception as e:
            # Index might already exist
            logging.debug(f"Entity FTS index creation: {e}")

        try:
            # Edge table FTS index
            self.conn.execute(
                """
                CALL CREATE_FTS_INDEX('RelatesToNode_', 'edge_name_and_fact', ['name', 'fact'])
            """
            )
        except Exception as e:
            # Index might already exist
            logging.debug(f"Edge FTS index creation: {e}")

    async def execute_query(
        self, cypher_query: str, **kwargs: Any
    ) -> tuple[list[dict[str, Any]] | list[list[dict[str, Any]]], None, None]:
        """Execute Cypher query."""
        # Don't filter None values - LadybugDB needs all referenced parameters
        params = dict(kwargs)
        params.pop("database_", None)
        params.pop("routing_", None)

        try:
            result = self.conn.execute(cypher_query, params)
            # Convert LadybugDB result to list of dicts
            column_names = result.get_column_names()
            records = []
            while result.has_next():
                row = result.get_next()
                # Convert row list to dict using column names
                record_dict = {col: row[i] for i, col in enumerate(column_names)}
                records.append(record_dict)
            return records, None, None
        except Exception as e:
            params_preview = {
                k: (v[:5] if isinstance(v, list) else v) for k, v in params.items()
            }
            logging.error(
                f"LadybugDB query error: {e}\n{cypher_query}\n{params_preview}"
            )
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
        """Initialize Graphiti with LadybugDB and configured providers."""
        # Get database path from config (default to ~/.unified-mcp/graphiti)
        source = self.config.get("source", "capabilities/graphiti_ladybug")
        self.db_path = str(Path(source) / "data" / "graphiti.db")

        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Initializing Graphiti with LadybugDB at: {self.db_path}")

        # Create LadybugDB driver
        driver = LadybugDriver(db_path=self.db_path)

        # Get provider configuration from environment
        llm_provider = os.getenv("GRAPHITI_LLM_PROVIDER", "openai").lower()
        embedder_provider = os.getenv("GRAPHITI_EMBEDDER_PROVIDER", "openai").lower()
        llm_model = os.getenv("GRAPHITI_LLM_MODEL")
        embedder_model = os.getenv("GRAPHITI_EMBEDDER_MODEL")

        # Debug logging
        self.logger.info(
            f"Environment: GRAPHITI_LLM_PROVIDER={llm_provider}, "
            f"GRAPHITI_EMBEDDER_PROVIDER={embedder_provider}"
        )
        self.logger.info(f"Models: LLM={llm_model}, Embedder={embedder_model}")
        google_key_status = "set" if os.getenv("GOOGLE_API_KEY") else "not set"
        openai_key_status = "set" if os.getenv("OPENAI_API_KEY") else "not set"
        self.logger.info(
            f"API Keys: GOOGLE_API_KEY={google_key_status}, "
            f"OPENAI_API_KEY={openai_key_status}"
        )

        # Create LLM client based on provider
        if llm_provider == "google_ai" or llm_provider == "google":
            if not HAS_GEMINI:
                raise RuntimeError(
                    "Gemini provider requested but not available. "
                    "This should not happen as Gemini is included in graphiti-core"
                )
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "GOOGLE_API_KEY environment variable is required for Google AI"
                )

            config = LLMConfig(api_key=api_key, model=llm_model or "gemini-2.5-flash")
            llm_client = GeminiClient(config=config)
            self.logger.info(f"Using Gemini LLM: {llm_model or 'gemini-2.5-flash'}")

        elif llm_provider == "anthropic":
            if not HAS_ANTHROPIC:
                raise RuntimeError(
                    "Anthropic provider requested but not available. "
                    "Install with: pip install graphiti-core[anthropic]"
                )
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY environment variable is required for Anthropic"
                )

            llm_client = AnthropicClient(
                api_key=api_key, model=llm_model or "claude-3-5-sonnet-20241022"
            )
            self.logger.info(
                f"Using Anthropic LLM: {llm_model or 'claude-3-5-sonnet-20241022'}"
            )

        elif llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY environment variable is required for OpenAI"
                )

            llm_client = OpenAIClient(api_key=api_key, model=llm_model or "gpt-4o-mini")
            self.logger.info(f"Using OpenAI LLM: {llm_model or 'gpt-4o-mini'}")

        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

        # Create embedder based on provider
        if embedder_provider == "google_ai" or embedder_provider == "google":
            if not HAS_GEMINI:
                raise RuntimeError(
                    "Gemini embedder requested but not available. "
                    "This should not happen as Gemini is included in graphiti-core"
                )
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "GOOGLE_API_KEY environment variable is required for Google AI"
                )

            embedder_config = GeminiEmbedderConfig(
                api_key=api_key, embedding_model=embedder_model or "text-embedding-004"
            )
            embedder = GeminiEmbedder(config=embedder_config)
            self.logger.info(
                f"Using Gemini embedder: {embedder_model or 'text-embedding-004'}"
            )

        elif embedder_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY environment variable is required for OpenAI"
                )

            embedder = OpenAIEmbedder(
                api_key=api_key, model=embedder_model or "text-embedding-3-small"
            )
            self.logger.info(
                f"Using OpenAI embedder: {embedder_model or 'text-embedding-3-small'}"
            )

        else:
            raise ValueError(f"Unsupported embedder provider: {embedder_provider}")

        # Create cross-encoder (reranker) based on LLM provider
        # Use the same provider as the LLM for consistency
        if llm_provider == "google_ai" or llm_provider == "google":
            reranker_config = LLMConfig(
                api_key=os.getenv("GOOGLE_API_KEY"),
                model=os.getenv("GRAPHITI_RERANKER_MODEL") or "gemini-2.5-flash-lite",
            )
            cross_encoder = GeminiRerankerClient(config=reranker_config)
            self.logger.info(f"Using Gemini reranker: {reranker_config.model}")
        elif llm_provider == "openai":
            # For OpenAI, Graphiti will create default OpenAIRerankerClient if we pass None
            # But let's be explicit about it
            from graphiti_core.cross_encoder.client import OpenAIRerankerConfig
            from graphiti_core.cross_encoder.openai_reranker_client import (
                OpenAIRerankerClient,
            )

            reranker_config = OpenAIRerankerConfig(api_key=os.getenv("OPENAI_API_KEY"))
            cross_encoder = OpenAIRerankerClient(config=reranker_config)
            self.logger.info("Using OpenAI reranker")
        else:
            # For other providers, disable cross-encoder
            cross_encoder = None
            self.logger.info("Cross-encoder disabled (no reranker for this provider)")

        # Initialize Graphiti with configured providers
        self.graphiti = Graphiti(
            graph_driver=driver,
            llm_client=llm_client,
            embedder=embedder,
            cross_encoder=cross_encoder,
        )

        self.logger.info(
            f"Graphiti + LadybugDB initialized successfully "
            f"(LLM: {llm_provider}, Embedder: {embedder_provider})"
        )

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
                            "description": (
                                "Source description "
                                "(e.g., 'user conversation', 'documentation')"
                            ),
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

            # Handle different return types from Graphiti search
            if isinstance(results, list):
                # Results is a list of edges
                edges = results
                nodes = []
                episodes = []
            elif hasattr(results, "nodes"):
                # Results is a SearchResults object
                nodes = results.nodes
                edges = results.edges
                episodes = results.episodes
            else:
                # Unknown format, treat as empty
                nodes = []
                edges = []
                episodes = []

            # Format results
            formatted_results = {
                "nodes": [
                    {
                        "uuid": node.uuid,
                        "name": node.name,
                        "summary": getattr(node, "summary", None),
                        "type": type(node).__name__,
                    }
                    for node in nodes
                ],
                "edges": [
                    {
                        "uuid": edge.uuid,
                        "fact": edge.fact,
                        "source": (
                            edge.source_node_uuid
                            if hasattr(edge, "source_node_uuid")
                            else None
                        ),
                        "target": (
                            edge.target_node_uuid
                            if hasattr(edge, "target_node_uuid")
                            else None
                        ),
                    }
                    for edge in edges
                ],
                "episodes": [
                    {
                        "uuid": ep.uuid,
                        "name": ep.name,
                        "content": ep.content,
                        "valid_at": str(ep.valid_at),
                    }
                    for ep in episodes
                ],
            }

            return {
                "status": "success",
                "tool": "search_insights",
                "query": query,
                "results": formatted_results,
                "count": {
                    "nodes": len(nodes),
                    "edges": len(edges),
                    "episodes": len(episodes),
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
