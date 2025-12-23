"""
Integration Tests for Memory Search Handler
============================================

Tests ClaudeMemHandler integration with Claude-mem HTTP API.

Requirements:
- Claude-mem service running on localhost:37777
- npm start in claude-mem directory

These are integration tests and may be skipped if Claude-mem is not running.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from handlers.memory_search import ClaudeMemHandler


@pytest.fixture
def memory_config():
    """Configuration for memory search handler."""
    return {
        "type": "claude-mem",
        "source": "capabilities/claude-mem",
        "api_url": "http://localhost:37777",
        "enabled": True,
    }


@pytest.fixture
async def memory_handler(memory_config):
    """Create and initialize memory search handler."""
    handler = ClaudeMemHandler(memory_config)
    # Note: We'll mock HTTP calls to avoid dependency on running service
    return handler


class TestMemoryHandlerInitialization:
    """Tests for handler initialization."""

    @pytest.mark.asyncio
    async def test_handler_sets_api_url(self, memory_handler):
        """Handler uses configured API URL."""
        assert memory_handler.api_url == "http://localhost:37777"

    @pytest.mark.asyncio
    async def test_handler_initializes_http_client(self, memory_handler):
        """Handler initializes HTTP client on init."""
        await memory_handler.initialize()
        assert memory_handler.http_client is not None


class TestMemoryToolSchemas:
    """Tests for tool schema definitions."""

    @pytest.mark.asyncio
    async def test_mem_search_schema(self, memory_handler):
        """mem_search has correct schema."""
        schema = await memory_handler.get_tool_schema("mem_search")

        assert schema["name"] == "mem_search"
        assert "search" in schema["description"].lower()
        assert "query" in schema["input_schema"]["properties"]
        assert "limit" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["query"]

    @pytest.mark.asyncio
    async def test_mem_get_observation_schema(self, memory_handler):
        """mem_get_observation has correct schema."""
        schema = await memory_handler.get_tool_schema("mem_get_observation")

        assert schema["name"] == "mem_get_observation"
        assert "observation" in schema["description"].lower()
        assert "id" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["id"]

    @pytest.mark.asyncio
    async def test_mem_recent_context_schema(self, memory_handler):
        """mem_recent_context has correct schema."""
        schema = await memory_handler.get_tool_schema("mem_recent_context")

        assert schema["name"] == "mem_recent_context"
        assert "recent" in schema["description"].lower()
        assert "limit" in schema["input_schema"]["properties"]

    @pytest.mark.asyncio
    async def test_mem_timeline_schema(self, memory_handler):
        """mem_timeline has correct schema."""
        schema = await memory_handler.get_tool_schema("mem_timeline")

        assert schema["name"] == "mem_timeline"
        assert "timeline" in schema["description"].lower()
        assert "limit" in schema["input_schema"]["properties"]
        assert "start_date" in schema["input_schema"]["properties"]
        assert "end_date" in schema["input_schema"]["properties"]

    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self, memory_handler):
        """Unknown tool name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await memory_handler.get_tool_schema("nonexistent_tool")


class TestMemoryToolExecution:
    """Tests for tool execution with mocked HTTP client."""

    @pytest.mark.asyncio
    async def test_mem_search_execution(self, memory_handler):
        """mem_search makes correct HTTP POST request."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "observations": [{"id": 1, "content": "test"}]
        }
        mock_response.raise_for_status = Mock()

        # Mock httpx.AsyncClient
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await memory_handler.initialize()
            result = await memory_handler.execute(
                "mem_search", {"query": "test query", "limit": 5}
            )

            # Verify HTTP call
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "/api/search" in call_args[0][0]
            assert call_args[1]["json"]["query"] == "test query"
            assert call_args[1]["json"]["limit"] == 5

            # Verify result
            assert result["status"] == "success"
            assert result["tool"] == "mem_search"
            assert result["query"] == "test query"

    @pytest.mark.asyncio
    async def test_mem_get_observation_execution(self, memory_handler):
        """mem_get_observation makes correct HTTP GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123, "content": "observation data"}
        mock_response.raise_for_status = Mock()

        # Mock httpx.AsyncClient
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await memory_handler.initialize()
            result = await memory_handler.execute("mem_get_observation", {"id": 123})

            # Verify HTTP call - expect 2 calls (health check + actual API call)
            assert mock_client.get.call_count == 2
            # Check the second call (actual API call)
            actual_call = mock_client.get.call_args_list[1]
            assert "/api/observation/123" in actual_call[0][0]

            # Verify result
            assert result["status"] == "success"
            assert result["tool"] == "mem_get_observation"
            assert result["id"] == 123

    @pytest.mark.asyncio
    async def test_mem_recent_context_execution(self, memory_handler):
        """mem_recent_context makes correct HTTP GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"recent": []}
        mock_response.raise_for_status = Mock()

        # Mock httpx.AsyncClient
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await memory_handler.initialize()
            result = await memory_handler.execute("mem_recent_context", {"limit": 20})

            # Verify HTTP call - expect 2 calls (health check + actual API call)
            assert mock_client.get.call_count == 2
            # Check the second call (actual API call)
            actual_call = mock_client.get.call_args_list[1]
            assert "/api/recent" in actual_call[0][0]
            assert actual_call[1]["params"]["limit"] == 20

            # Verify result
            assert result["status"] == "success"
            assert result["tool"] == "mem_recent_context"

    @pytest.mark.asyncio
    async def test_mem_timeline_execution(self, memory_handler):
        """mem_timeline makes correct HTTP GET request with date filters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"timeline": []}
        mock_response.raise_for_status = Mock()

        # Mock httpx.AsyncClient
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await memory_handler.initialize()
            result = await memory_handler.execute(
                "mem_timeline",
                {"limit": 50, "start_date": "2024-01-01", "end_date": "2024-12-31"},
            )

            # Verify HTTP call - expect 2 calls (health check + actual API call)
            assert mock_client.get.call_count == 2
            # Check the second call (actual API call)
            actual_call = mock_client.get.call_args_list[1]
            assert "/api/timeline" in actual_call[0][0]
            assert actual_call[1]["params"]["limit"] == 50
            assert actual_call[1]["params"]["start_date"] == "2024-01-01"
            assert actual_call[1]["params"]["end_date"] == "2024-12-31"

            # Verify result
            assert result["status"] == "success"
            assert result["tool"] == "mem_timeline"

    @pytest.mark.asyncio
    async def test_unknown_tool_execution_raises_error(self, memory_handler):
        """Executing unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await memory_handler.execute("nonexistent_tool", {})


class TestMemoryAPIIntegration:
    """Tests for Claude-mem HTTP API integration."""

    def test_handler_uses_correct_api_url(self, memory_handler):
        """Handler uses correct Claude-mem API URL."""
        assert memory_handler.api_url == "http://localhost:37777"

    @pytest.mark.asyncio
    async def test_cleanup_method_exists(self, memory_handler):
        """Handler has cleanup method for HTTP client."""
        assert hasattr(memory_handler, "cleanup")
        assert callable(memory_handler.cleanup)

    @pytest.mark.asyncio
    async def test_cleanup_closes_http_client(self, memory_handler):
        """Cleanup properly closes HTTP client."""
        await memory_handler.initialize()

        with patch.object(memory_handler.http_client, "aclose") as mock_close:
            await memory_handler.cleanup()
            mock_close.assert_called_once()


class TestMemoryToolMapping:
    """Tests for tool mapping to Claude-mem API."""

    def test_search_maps_to_api_search(self):
        """mem_search maps to POST /api/search."""
        import inspect

        source = inspect.getsource(ClaudeMemHandler._search)
        assert "/api/search" in source
        assert "post" in source.lower()

    def test_get_observation_maps_to_api_observation(self):
        """mem_get_observation maps to GET /api/observation/:id."""
        import inspect

        source = inspect.getsource(ClaudeMemHandler._get_observation)
        assert "/api/observation" in source
        assert "get" in source.lower()

    def test_recent_context_maps_to_api_recent(self):
        """mem_recent_context maps to GET /api/recent."""
        import inspect

        source = inspect.getsource(ClaudeMemHandler._recent_context)
        assert "/api/recent" in source

    def test_timeline_maps_to_api_timeline(self):
        """mem_timeline maps to GET /api/timeline."""
        import inspect

        source = inspect.getsource(ClaudeMemHandler._timeline)
        assert "/api/timeline" in source
