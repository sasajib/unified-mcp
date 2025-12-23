#!/usr/bin/env python3
"""Test Context7 integration by resolving a library ID."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core import DynamicToolRegistry


async def test_context7():
    """Test Context7 library resolution."""

    # Initialize registry
    catalog_path = Path(__file__).parent / "config" / "catalog.yaml"
    registry = DynamicToolRegistry(catalog_path)

    print("Testing Context7 integration...")
    print("=" * 60)

    # Test resolve_library_id
    print("\n1. Testing resolve_library_id for 'unipile'...")
    try:
        result = await registry.execute_tool(
            "resolve_library_id",
            {"libraryName": "unipile"}
        )
        print(f"✅ Success! Result: {result}")

        # If we got a library ID, try to fetch docs
        if result.get("status") == "success" and "libraryId" in result:
            library_id = result["libraryId"]
            print(f"\n2. Testing get_library_docs for library ID: {library_id}...")

            docs_result = await registry.execute_tool(
                "get_library_docs",
                {"libraryId": library_id}
            )
            print(f"✅ Success! Got documentation with {len(str(docs_result))} characters")
            print(f"\nFirst 500 chars of docs:\n{str(docs_result)[:500]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✅ All Context7 tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_context7())
    sys.exit(0 if success else 1)
