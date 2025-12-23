#!/usr/bin/env python3
"""Test Graphiti with Gemini directly."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import os
print("Environment variables:")
print(f"  GRAPHITI_LLM_PROVIDER: {os.getenv('GRAPHITI_LLM_PROVIDER')}")
print(f"  GRAPHITI_EMBEDDER_PROVIDER: {os.getenv('GRAPHITI_EMBEDDER_PROVIDER')}")
print(f"  GRAPHITI_LLM_MODEL: {os.getenv('GRAPHITI_LLM_MODEL')}")
print(f"  GRAPHITI_EMBEDDER_MODEL: {os.getenv('GRAPHITI_EMBEDDER_MODEL')}")
print(f"  GOOGLE_API_KEY: {'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")
print()

from handlers.knowledge_graph import GraphitiHandler


async def test_graphiti():
    """Test Graphiti initialization with Gemini."""

    config = {
        "name": "knowledge_graph",
        "type": "graphiti_ladybug",
        "source": "capabilities/graphiti_ladybug",
        "enabled": True,
        "tools": ["search_insights", "store_insight"],
        "description": "Knowledge graph with Gemini"
    }

    print("Initializing GraphitiHandler...")
    handler = GraphitiHandler(config)

    try:
        await handler.initialize()
        print("✅ GraphitiHandler initialized successfully with Gemini!")
        print()

        # Try storing an insight
        print("Testing store_insight...")
        result = await handler.execute("store_insight", {
            "content": "The unified-mcp server consolidates 5 capabilities into a single MCP server with progressive discovery, achieving 96-160x token reduction.",
            "source": "test script"
        })
        print(f"✅ Stored insight: {result}")
        print()

        # Try searching
        print("Testing search_insights...")
        search_result = await handler.execute("search_insights", {
            "query": "unified MCP server",
            "limit": 3
        })
        print(f"✅ Search results: {search_result}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    print("✅ All tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_graphiti())
    sys.exit(0 if success else 1)
