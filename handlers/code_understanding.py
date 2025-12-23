"""
Codanna Handler
===============

Code understanding via Codanna CLI integration.

Maps unified-mcp tools to Codanna's MCP tools:
- search_code → semantic_search_with_context (natural language with relationships)
- get_call_graph → get_calls + find_callers (both call directions)
- find_symbol → find_symbol (exact symbol lookup)
- find_implementations → search_symbols (filtered by kind)
"""

import asyncio
import json
import shutil
from pathlib import Path
from typing import List, Optional

from core.capability_loader import CapabilityHandler


class CodannaHandler(CapabilityHandler):
    """Handler for Codanna code understanding tools."""

    def __init__(self, config: dict):
        """Initialize handler with config."""
        super().__init__(config)
        self.codanna_path: Optional[str] = None
        self.project_root: Path = Path.cwd()
        self.auto_index: bool = config.get("auto_index", True)  # Auto-index by default
        self.watch_changes: bool = config.get(
            "watch_changes", False
        )  # Watch disabled by default
        self.index_dirs: List[str] = config.get(
            "index_dirs", ["src", "lib", "."]
        )  # Directories to index

    async def initialize(self) -> None:
        """Initialize Codanna - verify installation and check index."""
        # Check if codanna is installed
        self.codanna_path = shutil.which("codanna")
        if not self.codanna_path:
            raise RuntimeError(
                "Codanna not found. Install with: cargo install codanna --all-features"
            )

        self.logger.info(f"Codanna found at: {self.codanna_path}")

        # Check if index exists in current project
        index_path = self.project_root / ".codanna" / "index"
        if not index_path.exists():
            if self.auto_index:
                self.logger.info(
                    f"Codanna index not found at {index_path}. Auto-indexing..."
                )
                await self._auto_index()
            else:
                self.logger.warning(
                    f"Codanna index not found at {index_path}. "
                    "Run 'codanna init && codanna index src --progress' to create index, "
                    "or enable auto_index in config."
                )
        else:
            self.logger.info(f"Codanna index found at {index_path}")

        # Start file watcher if enabled
        if self.watch_changes and index_path.exists():
            self.logger.info("Starting file watcher for automatic re-indexing...")
            asyncio.create_task(self._watch_and_reindex())

    async def _auto_index(self) -> None:
        """Automatically initialize and index the codebase."""
        try:
            # Run codanna init
            self.logger.info("Running: codanna init")
            init_proc = await asyncio.create_subprocess_exec(
                self.codanna_path,
                "init",
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await init_proc.communicate()

            if init_proc.returncode != 0:
                self.logger.error(f"codanna init failed: {stderr.decode()}")
                return

            # Find directories to index
            dirs_to_index = []
            for dir_name in self.index_dirs:
                dir_path = self.project_root / dir_name
                if dir_path.exists() and dir_path.is_dir():
                    dirs_to_index.append(dir_name)

            if not dirs_to_index:
                self.logger.warning("No source directories found to index")
                return

            # Run codanna index on discovered directories
            self.logger.info(f"Indexing directories: {', '.join(dirs_to_index)}")
            for dir_name in dirs_to_index:
                self.logger.info(f"Running: codanna index {dir_name}")
                index_proc = await asyncio.create_subprocess_exec(
                    self.codanna_path,
                    "index",
                    dir_name,
                    cwd=self.project_root,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await index_proc.communicate()

                if index_proc.returncode == 0:
                    self.logger.info(f"✓ Indexed {dir_name}")
                else:
                    self.logger.warning(
                        f"Failed to index {dir_name}: {stderr.decode()}"
                    )

            self.logger.info("✓ Auto-indexing completed")

        except Exception as e:
            self.logger.error(f"Auto-indexing failed: {e}")

    async def _watch_and_reindex(self) -> None:
        """Watch for file changes and re-index automatically."""
        try:
            import watchdog.events
            import watchdog.observers

            class CodeChangeHandler(watchdog.events.FileSystemEventHandler):
                def __init__(self, handler):
                    self.handler = handler
                    self.last_reindex = 0
                    self.reindex_delay = 5  # seconds

                def on_modified(self, event):
                    if event.is_directory:
                        return

                    # Only reindex for code files
                    if not any(
                        event.src_path.endswith(ext)
                        for ext in [
                            ".py",
                            ".js",
                            ".ts",
                            ".jsx",
                            ".tsx",
                            ".rs",
                            ".go",
                            ".java",
                            ".cpp",
                            ".c",
                            ".h",
                        ]
                    ):
                        return

                    # Debounce re-indexing
                    import time

                    now = time.time()
                    if now - self.last_reindex < self.reindex_delay:
                        return

                    self.last_reindex = now
                    self.handler.logger.info(
                        f"File changed: {event.src_path}. Re-indexing..."
                    )
                    asyncio.create_task(self.handler._auto_index())

            event_handler = CodeChangeHandler(self)
            observer = watchdog.observers.Observer()

            for dir_name in self.index_dirs:
                dir_path = self.project_root / dir_name
                if dir_path.exists():
                    observer.schedule(event_handler, str(dir_path), recursive=True)

            observer.start()
            self.logger.info("File watcher started")

        except ImportError:
            self.logger.warning(
                "watchdog package not installed. File watching disabled. "
                "Install with: pip install watchdog"
            )
        except Exception as e:
            self.logger.error(f"Failed to start file watcher: {e}")

    async def get_tool_schema(self, tool_name: str) -> dict:
        """Get JSON schema for a tool."""
        schemas = {
            "search_code": {
                "name": "search_code",
                "description": (
                    "Search codebase using natural language queries. "
                    "Returns semantically similar symbols with full context including "
                    "what calls them, what they call, and impact analysis."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Natural language search query "
                                "(e.g., 'authentication logic', 'error handling')"
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 5)",
                            "default": 5,
                        },
                        "threshold": {
                            "type": "number",
                            "description": "Minimum similarity score 0-1 (default: 0.7)",
                            "default": 0.7,
                        },
                        "lang": {
                            "type": "string",
                            "description": (
                                "Filter by language "
                                "(e.g., 'rust', 'typescript', 'python')"
                            ),
                        },
                    },
                    "required": ["query"],
                },
            },
            "get_call_graph": {
                "name": "get_call_graph",
                "description": (
                    "Get complete call graph for a function. "
                    "Shows both what the function calls (outgoing) and "
                    "what calls the function (incoming)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "function_name": {
                            "type": "string",
                            "description": "Function name to analyze",
                        },
                        "symbol_id": {
                            "type": "integer",
                            "description": "Symbol ID for unambiguous lookup (preferred over name)",
                        },
                    },
                    "oneOf": [
                        {"required": ["function_name"]},
                        {"required": ["symbol_id"]},
                    ],
                },
            },
            "find_symbol": {
                "name": "find_symbol",
                "description": (
                    "Find a symbol by exact name. "
                    "Returns symbol information including file path, "
                    "line number, kind, and signature. Sub-10ms lookup."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Exact symbol name to find",
                        }
                    },
                    "required": ["name"],
                },
            },
            "find_implementations": {
                "name": "find_implementations",
                "description": (
                    "Find implementations, classes, structs, or specific symbol kinds. "
                    "Uses fuzzy matching for flexible search."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (supports fuzzy matching)",
                        },
                        "kind": {
                            "type": "string",
                            "description": (
                                "Filter by kind: Function, Struct, "
                                "Class, Interface, Trait, etc."
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10,
                        },
                        "module": {
                            "type": "string",
                            "description": "Filter by module path",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

        if tool_name not in schemas:
            raise ValueError(f"Unknown tool: {tool_name}")

        return schemas[tool_name]

    async def execute(self, tool_name: str, arguments: dict) -> dict:
        """Execute a Codanna tool."""
        if tool_name == "search_code":
            return await self._search_code(arguments)
        elif tool_name == "get_call_graph":
            return await self._get_call_graph(arguments)
        elif tool_name == "find_symbol":
            return await self._find_symbol(arguments)
        elif tool_name == "find_implementations":
            return await self._find_implementations(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _search_code(self, args: dict) -> dict:
        """
        Search code using semantic_search_with_context.

        Maps to: codanna mcp semantic_search_with_context query:"..." [options]
        """
        query = args["query"]
        limit = args.get("limit", 5)
        threshold = args.get("threshold", 0.7)
        lang = args.get("lang")

        cmd = [
            self.codanna_path,
            "mcp",
            "semantic_search_with_context",
            f"query:{query}",
            f"limit:{limit}",
            f"threshold:{threshold}",
            "--json",
        ]

        if lang:
            cmd.append(f"lang:{lang}")

        result = await self._run_codanna_command(cmd)
        return {
            "status": "success",
            "tool": "search_code",
            "query": query,
            "results": result.get("data", []),
        }

    async def _get_call_graph(self, args: dict) -> dict:
        """
        Get call graph (both directions).

        Combines get_calls (outgoing) and find_callers (incoming).
        """
        function_name = args.get("function_name")
        symbol_id = args.get("symbol_id")

        if not function_name and not symbol_id:
            raise ValueError("Either function_name or symbol_id required")

        # Build identifier
        identifier = f"symbol_id:{symbol_id}" if symbol_id else function_name

        # Get outgoing calls
        outgoing_cmd = [
            self.codanna_path,
            "mcp",
            "get_calls",
            identifier,
            "--json",
        ]
        outgoing = await self._run_codanna_command(outgoing_cmd)

        # Get incoming calls
        incoming_cmd = [
            self.codanna_path,
            "mcp",
            "find_callers",
            identifier,
            "--json",
        ]
        incoming = await self._run_codanna_command(incoming_cmd)

        return {
            "status": "success",
            "tool": "get_call_graph",
            "function": function_name or f"symbol_id:{symbol_id}",
            "outgoing_calls": outgoing.get("data", []),
            "incoming_calls": incoming.get("data", []),
        }

    async def _find_symbol(self, args: dict) -> dict:
        """
        Find symbol by exact name.

        Maps to: codanna mcp find_symbol <name>
        """
        name = args["name"]

        cmd = [
            self.codanna_path,
            "mcp",
            "find_symbol",
            name,
            "--json",
        ]

        result = await self._run_codanna_command(cmd)
        return {
            "status": "success",
            "tool": "find_symbol",
            "name": name,
            "results": result.get("data", []),
        }

    async def _find_implementations(self, args: dict) -> dict:
        """
        Find implementations using search_symbols.

        Maps to: codanna mcp search_symbols query:"..." [kind:...] [options]
        """
        query = args["query"]
        kind = args.get("kind")
        limit = args.get("limit", 10)
        module = args.get("module")

        cmd = [
            self.codanna_path,
            "mcp",
            "search_symbols",
            f"query:{query}",
            f"limit:{limit}",
            "--json",
        ]

        if kind:
            cmd.append(f"kind:{kind}")
        if module:
            cmd.append(f"module:{module}")

        result = await self._run_codanna_command(cmd)
        return {
            "status": "success",
            "tool": "find_implementations",
            "query": query,
            "kind": kind,
            "results": result.get("data", []),
        }

    async def _run_codanna_command(self, cmd: List[str]) -> dict:
        """
        Run a codanna CLI command and parse JSON output.

        Args:
            cmd: Command and arguments as list

        Returns:
            Parsed JSON result from codanna

        Raises:
            RuntimeError: If command fails or returns invalid JSON
        """
        try:
            self.logger.debug(f"Running: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root),
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8").strip()
                self.logger.error(f"Codanna command failed: {error_msg}")
                raise RuntimeError(f"Codanna error: {error_msg}")

            output = stdout.decode("utf-8").strip()

            # Parse JSON output
            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON from Codanna: {output[:200]}")
                raise RuntimeError(f"Invalid JSON from Codanna: {e}")

        except FileNotFoundError:
            raise RuntimeError(
                f"Codanna executable not found at {self.codanna_path}. "
                "Install with: cargo install codanna --all-features"
            )
        except Exception as e:
            self.logger.error(f"Error running Codanna: {e}")
            raise
