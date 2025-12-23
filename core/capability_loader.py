"""
Capability Loader
=================

Plugin system for loading capability handlers.

Provides base class and factory for creating handlers that wrap external
tools and services (Codanna, Context7, Playwright, etc.).
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CapabilityHandler(ABC):
    """
    Base class for all capability handlers.

    Each capability (Codanna, Context7, Playwright, etc.) implements
    this interface to provide a unified async API for tool execution.

    Pattern:
    1. Initialize handler with source path
    2. Call initialize() to set up dependencies
    3. Use get_tool_schema() to get tool definitions
    4. Use execute() to run tools
    """

    def __init__(self, source_path: Path):
        """
        Initialize handler.

        Args:
            source_path: Path to capability source (git submodule, etc.)
        """
        self.source_path = source_path
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the capability.

        This may involve:
        - Checking if external tools are installed
        - Starting background services
        - Creating indexes or caches
        - Validating configuration

        Raises:
            RuntimeError: If initialization fails
        """
        pass

    @abstractmethod
    async def get_tool_schema(self, tool_name: str) -> dict:
        """
        Get JSON schema for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            JSON schema dict with:
            - name: Tool name
            - description: What the tool does
            - input_schema: JSON schema for input parameters
            - output_schema: Optional JSON schema for output
            - examples: Optional list of usage examples

        Example:
            {
                'name': 'search_code',
                'description': 'Search codebase semantically',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'query': {'type': 'string', 'description': '...'},
                        'language': {'type': 'string', 'description': '...'}
                    },
                    'required': ['query']
                }
            }
        """
        pass

    @abstractmethod
    async def execute(self, tool_name: str, arguments: dict) -> dict:
        """
        Execute a tool.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments as dict

        Returns:
            Tool execution result as dict

        Raises:
            ValueError: If tool_name is unknown
            Exception: If execution fails

        Example:
            >>> result = await handler.execute(
            ...     'search_code',
            ...     {'query': 'authentication'}
            ... )
        """
        pass

    async def cleanup(self) -> None:
        """
        Clean up resources (optional).

        Override this to:
        - Close connections
        - Stop background processes
        - Free memory
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} at {self.source_path}>"


class CapabilityLoader:
    """
    Factory for creating capability handlers.

    Loads the appropriate handler class based on capability type.
    """

    @staticmethod
    async def load_handler(
        capability_type: str, source_path: Path, **kwargs
    ) -> CapabilityHandler:
        """
        Load appropriate handler based on capability type.

        Args:
            capability_type: Type identifier (e.g., "codanna", "context7")
            source_path: Path to capability source
            **kwargs: Additional arguments for handler constructor

        Returns:
            Initialized CapabilityHandler instance

        Raises:
            ValueError: If capability_type is unknown
            ImportError: If handler module cannot be imported

        Example:
            >>> handler = await CapabilityLoader.load_handler(
            ...     "codanna",
            ...     Path("capabilities/codanna")
            ... )
        """
        logger.debug(f"Loading handler for type: {capability_type}")

        try:
            if capability_type == "codanna":
                from handlers.code_understanding import CodannaHandler

                handler = CodannaHandler(source_path, **kwargs)

            elif capability_type == "context7":
                from handlers.documentation import Context7Handler

                handler = Context7Handler(source_path, **kwargs)

            elif capability_type == "playwright":
                from handlers.browser_automation import PlaywrightHandler

                handler = PlaywrightHandler(source_path, **kwargs)

            elif capability_type == "claude-mem":
                from handlers.memory_search import ClaudeMemHandler

                handler = ClaudeMemHandler(source_path, **kwargs)

            elif capability_type == "graphiti_ladybug":
                from handlers.knowledge_graph import GraphitiHandler

                handler = GraphitiHandler(source_path, **kwargs)

            else:
                raise ValueError(f"Unknown capability type: {capability_type}")

            # Initialize handler
            await handler.initialize()

            logger.info(f"Handler loaded: {capability_type}")
            return handler

        except ImportError as e:
            logger.error(f"Failed to import handler for {capability_type}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load handler for {capability_type}: {e}")
            raise


# Utility functions for handlers


def validate_tool_arguments(arguments: dict, schema: dict) -> bool:
    """
    Validate tool arguments against JSON schema.

    Args:
        arguments: Arguments to validate
        schema: JSON schema

    Returns:
        True if valid, False otherwise

    Note:
        This is a simplified validator. For production, use jsonschema library.
    """
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    # Check required fields
    for field in required:
        if field not in arguments:
            logger.error(f"Missing required field: {field}")
            return False

    # Check field types (simplified)
    for field, value in arguments.items():
        if field in properties:
            expected_type = properties[field].get("type")
            actual_type = type(value).__name__

            # Simple type mapping
            type_map = {
                "str": "string",
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "dict": "object",
                "list": "array",
            }

            if type_map.get(actual_type) != expected_type:
                logger.warning(
                    f"Type mismatch for {field}: expected {expected_type}, "
                    f"got {actual_type}"
                )

    return True


def create_error_response(error: Exception) -> dict:
    """
    Create standardized error response.

    Args:
        error: Exception that occurred

    Returns:
        Error response dict

    Example:
        >>> try:
        ...     # something that fails
        ... except Exception as e:
        ...     return create_error_response(e)
        {'error': 'ValueError', 'message': 'Invalid argument', 'success': False}
    """
    return {
        "success": False,
        "error": error.__class__.__name__,
        "message": str(error),
    }


def create_success_response(data: Any) -> dict:
    """
    Create standardized success response.

    Args:
        data: Response data

    Returns:
        Success response dict

    Example:
        >>> result = create_success_response({'results': [...]})
        {'success': True, 'data': {'results': [...]}}
    """
    return {
        "success": True,
        "data": data,
    }
