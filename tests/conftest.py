"""
Test Fixtures
=============

Shared pytest fixtures for unified-mcp tests.

Following Auto-Claude testing patterns with fixture composition.
"""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest
import yaml


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Temporary directory cleaned up after test."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    import shutil

    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_catalog_dict() -> dict:
    """Sample catalog configuration as dict."""
    return {
        "capabilities": {
            "test_capability": {
                "enabled": True,
                "type": "codanna",
                "source": "capabilities/codanna",
                "tools": ["test_tool_1", "test_tool_2"],
                "lazy_load": True,
                "description": "Test capability for unit tests",
            },
            "disabled_capability": {
                "enabled": False,
                "type": "context7",
                "source": "capabilities/context7",
                "tools": ["disabled_tool"],
                "lazy_load": True,
                "description": "Disabled test capability",
            },
        },
        "discovery": {
            "mode": "progressive",
            "search_only_tokens": 50,
            "describe_only_tokens": 200,
            "max_tools_in_context": 10,
        },
    }


@pytest.fixture
def sample_catalog(temp_dir: Path, sample_catalog_dict: dict) -> Path:
    """
    Create sample catalog.yaml for testing.

    Returns path to the catalog file.
    """
    catalog_path = temp_dir / "catalog.yaml"
    with open(catalog_path, "w") as f:
        yaml.dump(sample_catalog_dict, f)
    return catalog_path


@pytest.fixture
def sample_catalog_with_multiple_caps(temp_dir: Path) -> Path:
    """Catalog with multiple enabled capabilities."""
    catalog_data = {
        "capabilities": {
            "code_understanding": {
                "enabled": True,
                "type": "codanna",
                "source": "capabilities/codanna",
                "tools": ["search_code", "get_call_graph", "find_symbol"],
                "lazy_load": True,
                "description": "Code understanding tools",
            },
            "documentation": {
                "enabled": True,
                "type": "context7",
                "source": "capabilities/context7",
                "tools": ["resolve_library_id", "get_library_docs"],
                "lazy_load": True,
                "description": "Documentation tools",
            },
            "browser_automation": {
                "enabled": False,
                "type": "playwright",
                "source": "capabilities/playwright-mcp",
                "tools": ["playwright_navigate", "playwright_click"],
                "lazy_load": True,
                "description": "Browser automation (disabled)",
            },
        },
        "discovery": {
            "mode": "progressive",
            "search_only_tokens": 50,
            "describe_only_tokens": 200,
            "max_tools_in_context": 10,
        },
    }

    catalog_path = temp_dir / "catalog.yaml"
    with open(catalog_path, "w") as f:
        yaml.dump(catalog_data, f)

    return catalog_path
