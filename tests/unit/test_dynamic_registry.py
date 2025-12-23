"""
Tests for Dynamic Tool Registry
================================

Unit tests for core.dynamic_registry module.
"""

import pytest

from core.dynamic_registry import DynamicToolRegistry, ToolCapability


class TestToolCapability:
    """Tests for ToolCapability class."""

    def test_create_capability(self, sample_catalog_dict):
        """Create a capability from config dict."""
        config = sample_catalog_dict["capabilities"]["test_capability"]
        capability = ToolCapability("test_capability", config)

        assert capability.name == "test_capability"
        assert capability.enabled is True
        assert capability.type == "codanna"
        assert capability.tools == ["test_tool_1", "test_tool_2"]
        assert capability.lazy_load is True
        assert capability.is_loaded() is False

    def test_capability_defaults(self):
        """Capability uses defaults for optional fields."""
        config = {"type": "test", "source": "/tmp/test"}
        capability = ToolCapability("test", config)

        assert capability.enabled is False  # Default
        assert capability.tools == []  # Default
        assert capability.lazy_load is True  # Default

    def test_capability_repr(self, sample_catalog_dict):
        """Capability has useful repr."""
        config = sample_catalog_dict["capabilities"]["test_capability"]
        capability = ToolCapability("test_cap", config)

        repr_str = repr(capability)
        assert "ToolCapability" in repr_str
        assert "test_cap" in repr_str
        assert "unloaded" in repr_str


class TestDynamicToolRegistry:
    """Tests for DynamicToolRegistry class."""

    def test_load_catalog(self, sample_catalog):
        """Registry loads catalog from YAML file."""
        registry = DynamicToolRegistry(sample_catalog)

        assert len(registry.capabilities) == 2
        assert "test_capability" in registry.capabilities
        assert "disabled_capability" in registry.capabilities

    def test_catalog_not_found(self, temp_dir):
        """Registry raises error if catalog doesn't exist."""
        nonexistent = temp_dir / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            DynamicToolRegistry(nonexistent)

    @pytest.mark.asyncio
    async def test_search_tools(self, sample_catalog_with_multiple_caps):
        """Search tools finds matching tools."""
        registry = DynamicToolRegistry(sample_catalog_with_multiple_caps)

        # Search for "code"
        results = await registry.search_tools("code")

        assert len(results) > 0
        # Should find tools from code_understanding capability
        tool_names = [r["name"] for r in results]
        assert "search_code" in tool_names

    @pytest.mark.asyncio
    async def test_search_tools_max_results(self, sample_catalog_with_multiple_caps):
        """Search tools respects max_results limit."""
        registry = DynamicToolRegistry(sample_catalog_with_multiple_caps)

        results = await registry.search_tools("", max_results=2)

        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_search_tools_no_matches(self, sample_catalog):
        """Search tools returns empty list if no matches."""
        registry = DynamicToolRegistry(sample_catalog)

        results = await registry.search_tools("nonexistent_query_xyz")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_ignores_disabled_capabilities(
        self, sample_catalog_with_multiple_caps
    ):
        """Search tools ignores disabled capabilities."""
        registry = DynamicToolRegistry(sample_catalog_with_multiple_caps)

        # browser_automation is disabled
        results = await registry.search_tools("playwright")

        # Should not find playwright tools (capability is disabled)
        tool_names = [r["name"] for r in results]
        assert not any("playwright" in name for name in tool_names)

    @pytest.mark.asyncio
    async def test_describe_tools(self, sample_catalog):
        """Describe tools returns schemas (stub implementation)."""
        registry = DynamicToolRegistry(sample_catalog)

        # Note: This will use stub handler since submodules aren't set up
        schemas = await registry.describe_tools(["test_tool_1"])

        assert len(schemas) == 1
        assert schemas[0]["name"] == "test_tool_1"

    @pytest.mark.asyncio
    async def test_describe_unknown_tool(self, sample_catalog):
        """Describe tools handles unknown tools gracefully."""
        registry = DynamicToolRegistry(sample_catalog)

        schemas = await registry.describe_tools(["unknown_tool"])

        # Should return empty list (tool not found in any capability)
        assert schemas == []

    @pytest.mark.asyncio
    async def test_enable_capability(self, sample_catalog):
        """Can enable a disabled capability."""
        registry = DynamicToolRegistry(sample_catalog)

        # Initially disabled
        assert registry.capabilities["disabled_capability"].enabled is False

        # Enable it
        result = await registry.enable_capability("disabled_capability")

        assert result["status"] == "Capability 'disabled_capability' enabled"
        assert registry.capabilities["disabled_capability"].enabled is True

    @pytest.mark.asyncio
    async def test_disable_capability(self, sample_catalog):
        """Can disable an enabled capability."""
        registry = DynamicToolRegistry(sample_catalog)

        # Initially enabled
        assert registry.capabilities["test_capability"].enabled is True

        # Disable it
        result = await registry.disable_capability("test_capability")

        assert result["status"] == "Capability 'test_capability' disabled"
        assert registry.capabilities["test_capability"].enabled is False

    @pytest.mark.asyncio
    async def test_get_enabled_capabilities(self, sample_catalog_with_multiple_caps):
        """Get enabled capabilities returns only enabled ones."""
        registry = DynamicToolRegistry(sample_catalog_with_multiple_caps)

        enabled = await registry.get_enabled_capabilities()

        assert "code_understanding" in enabled
        assert "documentation" in enabled
        assert "browser_automation" not in enabled  # Disabled

    @pytest.mark.asyncio
    async def test_get_all_capabilities(self, sample_catalog_with_multiple_caps):
        """Get all capabilities returns info for all."""
        registry = DynamicToolRegistry(sample_catalog_with_multiple_caps)

        all_caps = await registry.get_all_capabilities()

        assert len(all_caps) == 3
        assert all(isinstance(cap, dict) for cap in all_caps)
        assert all("name" in cap for cap in all_caps)
        assert all("enabled" in cap for cap in all_caps)

    def test_get_discovery_config(self, sample_catalog):
        """Get discovery config returns catalog discovery settings."""
        registry = DynamicToolRegistry(sample_catalog)

        config = registry.get_discovery_config()

        assert config["mode"] == "progressive"
        assert config["search_only_tokens"] == 50
        assert config["describe_only_tokens"] == 200

    def test_find_capability_for_tool(self, sample_catalog):
        """Can find which capability provides a tool."""
        registry = DynamicToolRegistry(sample_catalog)

        capability = registry._find_capability_for_tool("test_tool_1")

        assert capability is not None
        assert capability.name == "test_capability"

    def test_find_capability_for_unknown_tool(self, sample_catalog):
        """Returns None for unknown tool."""
        registry = DynamicToolRegistry(sample_catalog)

        capability = registry._find_capability_for_tool("unknown_tool")

        assert capability is None

    def test_get_short_description(self, sample_catalog):
        """Get short description for known tools."""
        registry = DynamicToolRegistry(sample_catalog)

        # Known tool
        desc = registry._get_short_description("search_code")
        assert desc == "Search codebase semantically"

        # Unknown tool
        desc = registry._get_short_description("unknown_tool")
        assert desc == "No description available"
