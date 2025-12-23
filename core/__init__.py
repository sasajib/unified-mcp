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

from .dynamic_registry import DynamicToolRegistry, ToolCapability
from .progressive_discovery import (
    search_tools,
    describe_tools,
    execute_tool,
    ToolPreview,
    ToolSchema,
)
from .capability_loader import CapabilityHandler, CapabilityLoader

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
