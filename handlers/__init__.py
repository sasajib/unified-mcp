"""
Handlers Module
===============

Capability handlers for external tools and services.

Each handler wraps an external capability (Codanna, Context7, Playwright,
Claude-mem, Graphiti) with a unified async interface.
"""

__all__ = [
    "CodannaHandler",
    "Context7Handler",
    "PlaywrightHandler",
    "ClaudeMemHandler",
    "GraphitiHandler",
]
