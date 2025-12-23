import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from handlers.code_understanding import CodannaHandler
from handlers.documentation import Context7Handler
from handlers.browser_automation import PlaywrightHandler
from handlers.memory_search import ClaudeMemHandler
from handlers.knowledge_graph import GraphitiHandler

async def test_all_capabilities():
    """Test one tool from each of the 5 capabilities."""

    print("=" * 70)
    print("Testing All 5 Unified-MCP Capabilities")
    print("=" * 70)

    results = []
    base_path = Path(__file__).parent

    # Test 1: Code Understanding (Codanna)
    print("\n1. Testing Code Understanding (Codanna)...")
    try:
        config = {
            "name": "code_understanding",
            "type": "codanna",
            "source": str(base_path / "capabilities/codanna"),
            "enabled": True,
        }
        handler = CodannaHandler(config)
        await handler.initialize()
        result = await handler.execute("search_code", {
            "query": "async def",
            "max_results": 3
        })
        count = len(result.get('results', []))
        print(f"   ✅ Code Understanding - found {count} code matches")
        results.append(("Code Understanding (Codanna)", True, f"{count} results"))
    except Exception as e:
        print(f"   ❌ Code Understanding failed: {e}")
        results.append(("Code Understanding (Codanna)", False, str(e)[:50]))
    
    # Test 2: Documentation (Context7)
    print("\n2. Testing Documentation (Context7)...")
    try:
        config = {
            "name": "documentation",
            "type": "context7",
            "source": str(base_path / "capabilities/context7"),
            "enabled": True,
        }
        handler = Context7Handler(config)
        await handler.initialize()
        result = await handler.execute("resolve_library_id", {
            "libraryName": "react"
        })
        library_id = result.get('library_id', 'unknown')
        print(f"   ✅ Documentation - resolved React to: {library_id}")
        results.append(("Documentation (Context7)", True, f"Resolved: {library_id}"))
    except Exception as e:
        print(f"   ❌ Documentation failed: {e}")
        results.append(("Documentation (Context7)", False, str(e)[:50]))

    # Test 3: Browser Automation (Playwright)
    print("\n3. Testing Browser Automation (Playwright)...")
    try:
        config = {
            "name": "browser_automation",
            "type": "playwright",
            "source": str(base_path / "capabilities/playwright-mcp"),
            "enabled": True,
        }
        handler = PlaywrightHandler(config)
        await handler.initialize()
        # Just check that handler initialized
        print(f"   ✅ Browser Automation - initialized successfully")
        results.append(("Browser Automation (Playwright)", True, "Initialized"))
    except Exception as e:
        print(f"   ❌ Browser Automation failed: {e}")
        results.append(("Browser Automation (Playwright)", False, str(e)[:50]))

    # Test 4: Memory Search (Claude-mem)
    print("\n4. Testing Memory Search (Claude-mem)...")
    try:
        config = {
            "name": "memory_search",
            "type": "claude-mem",
            "source": str(base_path / "capabilities/claude-mem"),
            "enabled": True,
            "api_url": "http://localhost:37777"
        }
        handler = ClaudeMemHandler(config)
        await handler.initialize()
        result = await handler.execute("mem_search", {
            "query": "test",
            "limit": 3
        })
        count = len(result.get('results', []))
        print(f"   ✅ Memory Search - found {count} memories")
        results.append(("Memory Search (Claude-mem)", True, f"{count} memories"))
    except Exception as e:
        print(f"   ❌ Memory Search failed: {e}")
        results.append(("Memory Search (Claude-mem)", False, str(e)[:50]))

    # Test 5: Knowledge Graph (Graphiti with Gemini)
    print("\n5. Testing Knowledge Graph (Graphiti with Gemini)...")
    try:
        config = {
            "name": "knowledge_graph",
            "type": "graphiti_ladybug",
            "source": str(base_path / "capabilities/graphiti_ladybug"),
            "enabled": True,
        }
        handler = GraphitiHandler(config)
        await handler.initialize()
        result = await handler.execute("search_insights", {
            "query": "unified-mcp",
            "limit": 3
        })
        edge_count = result.get('count', {}).get('edges', 0)
        print(f"   ✅ Knowledge Graph (Gemini) - found {edge_count} edges")
        results.append(("Knowledge Graph (Graphiti+Gemini)", True, f"{edge_count} edges"))
    except Exception as e:
        print(f"   ❌ Knowledge Graph failed: {e}")
        results.append(("Knowledge Graph (Graphiti+Gemini)", False, str(e)[:50]))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, details in results:
        status = "✅" if success else "❌"
        print(f"{status} {name:40} {details}")
    
    print(f"\nTotal: {passed}/{total} capabilities working")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_all_capabilities())
