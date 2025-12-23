"""
Tests for Progressive Discovery Engine
=======================================

Unit tests for core.progressive_discovery module.
"""

import pytest

from core.dynamic_registry import DynamicToolRegistry
from core.progressive_discovery import (
    ToolPreview,
    ToolSchema,
    search_tools,
    describe_tools,
    estimate_token_cost,
    format_preview_for_display,
)


class TestSearchTools:
    """Tests for search_tools function."""

    @pytest.mark.asyncio
    async def test_search_tools(self, sample_catalog_with_multiple_caps):
        """Search tools returns ToolPreview objects."""
        registry = DynamicToolRegistry(sample_catalog_with_multiple_caps)

        previews = await search_tools(registry, "code")

        assert len(previews) > 0
        assert all(isinstance(p, ToolPreview) for p in previews)

    @pytest.mark.asyncio
    async def test_search_tools_attributes(self, sample_catalog_with_multiple_caps):
        """ToolPreview has required attributes."""
        registry = DynamicToolRegistry(sample_catalog_with_multiple_caps)

        previews = await search_tools(registry, "search")

        if previews:  # If any results found
            preview = previews[0]
            assert hasattr(preview, "name")
            assert hasattr(preview, "capability")
            assert hasattr(preview, "description")
            assert hasattr(preview, "tokens_estimate")


class TestDescribeTools:
    """Tests for describe_tools function."""

    @pytest.mark.asyncio
    async def test_describe_tools(self, sample_catalog):
        """Describe tools returns ToolSchema objects."""
        from unittest.mock import AsyncMock, patch

        registry = DynamicToolRegistry(sample_catalog)

        # Mock the registry's describe_tools to return a schema
        mock_schema = {
            "name": "test_tool_1",
            "description": "Test tool",
            "input_schema": {
                "type": "object",
                "properties": {"param": {"type": "string"}},
                "required": ["param"],
            },
        }

        with patch.object(
            registry, "describe_tools", new=AsyncMock(return_value=[mock_schema])
        ):
            schemas = await describe_tools(registry, ["test_tool_1"])

        assert len(schemas) == 1
        assert isinstance(schemas[0], ToolSchema)

    @pytest.mark.asyncio
    async def test_tool_schema_attributes(self, sample_catalog):
        """ToolSchema has required attributes."""
        from unittest.mock import AsyncMock, patch

        registry = DynamicToolRegistry(sample_catalog)

        # Mock the registry's describe_tools
        mock_schema = {
            "name": "test_tool_1",
            "description": "Test tool",
            "input_schema": {"type": "object", "properties": {}},
        }

        with patch.object(
            registry, "describe_tools", new=AsyncMock(return_value=[mock_schema])
        ):
            schemas = await describe_tools(registry, ["test_tool_1"])

        if schemas:
            schema = schemas[0]
            assert hasattr(schema, "name")
            assert hasattr(schema, "description")
            assert hasattr(schema, "input_schema")


class TestTokenEstimation:
    """Tests for token cost estimation."""

    def test_estimate_token_cost_preview_only(self):
        """Estimate cost for preview only."""
        cost = estimate_token_cost(num_previews=10)

        assert cost["preview_tokens"] == 50  # 10 * 5
        assert cost["schema_tokens"] == 0
        assert cost["execution_tokens"] == 0
        assert cost["total_tokens"] == 50

    def test_estimate_token_cost_with_schemas(self):
        """Estimate cost with schemas."""
        cost = estimate_token_cost(num_previews=10, num_schemas=2)

        assert cost["preview_tokens"] == 50
        assert cost["schema_tokens"] == 400  # 2 * 200
        assert cost["total_tokens"] == 450

    def test_estimate_token_cost_reduction_factor(self):
        """Estimate shows reduction vs static loading."""
        cost = estimate_token_cost(num_previews=10, num_schemas=2)

        # Should show significant reduction
        assert cost["reduction_factor"] > 1
        assert cost["vs_static_loading"] == 10000


class TestFormatting:
    """Tests for display formatting functions."""

    def test_format_preview_for_display(self):
        """Format preview for display."""
        preview = ToolPreview(
            name="search_code",
            capability="code_understanding",
            description="Search code",
            tokens_estimate=200,
        )

        formatted = format_preview_for_display(preview)

        assert "search_code" in formatted
        assert "code_understanding" in formatted
        assert "Search code" in formatted
        assert "200" in formatted
