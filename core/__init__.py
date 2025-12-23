"""
Core Module
===========

Core components for the unified dynamic MCP server.

This module provides:
- Dynamic tool registry with lazy loading
- Progressive discovery engine (96-160x token reduction)
- Capability loader plugin system
- MCP protocol utilities
"""

from .capability_loader import CapabilityHandler, CapabilityLoader
from .dynamic_registry import DynamicToolRegistry, ToolCapability
from .progressive_discovery import (
    ToolPreview,
    ToolSchema,
    describe_tools,
    execute_tool,
    search_tools,
)

__all__ = [
    "DynamicToolRegistry",
    "ToolCapability",
    "search_tools",
    "describe_tools",
    "execute_tool",
    "ToolPreview",
    "ToolSchema",
    "CapabilityHandler",
    "CapabilityLoader",
]
