"""
Example 2: Multi-Capability Workflow
====================================

This example demonstrates using multiple capabilities together
in a realistic workflow.
"""

import asyncio
import json


async def multi_capability_workflow():
    """Demonstrate using multiple capabilities together."""
    
    print("=" * 60)
    print("Multi-Capability Workflow Example")
    print("=" * 60)
    print()
    print("Scenario: Building a new feature with documentation")
    print()
    
    # Step 1: Search codebase for similar implementations
    print("STEP 1: Search existing code (Codanna)")
    print("-" * 60)
    
    search_result = {
        "status": "success",
        "tool": "search_code",
        "results": [
            {
                "file": "features/user_profile.py",
                "line": 23,
                "snippet": "class UserProfileFeature:"
            }
        ]
    }
    
    print(f"Found existing patterns: {json.dumps(search_result, indent=2)}")
    print()
    
    # Step 2: Get documentation for libraries we'll use
    print("STEP 2: Fetch library documentation (Context7)")
    print("-" * 60)
    
    doc_result = {
        "status": "success",
        "tool": "get_library_docs",
        "libraryID": "/facebook/react",
        "topic": "hooks",
        "results": [
            {
                "title": "useState Hook",
                "description": "Returns stateful value and updater function"
            }
        ]
    }
    
    print(f"Documentation retrieved: {json.dumps(doc_result, indent=2)}")
    print()
    
    # Step 3: Store implementation insights
    print("STEP 3: Store implementation insights (Graphiti)")
    print("-" * 60)
    
    insight = {
        "content": (
            "UserProfile feature follows pattern: "
            "1. Create state with useState, "
            "2. Fetch data in useEffect, "
            "3. Render with loading states"
        ),
        "source": "codebase analysis"
    }
    
    graph_result = {
        "status": "success",
        "tool": "store_insight",
        "message": "Insight stored successfully"
    }
    
    print(f"Stored insight: {json.dumps(insight, indent=2)}")
    print(f"Result: {json.dumps(graph_result, indent=2)}")
    print()
    
    # Step 4: Test the implementation
    print("STEP 4: Test in browser (Playwright)")
    print("-" * 60)
    
    test_steps = [
        {
            "tool": "playwright_navigate",
            "args": {"url": "http://localhost:3000/profile"},
            "result": {"status": "success", "url": "http://localhost:3000/profile"}
        },
        {
            "tool": "playwright_screenshot",
            "args": {"filename": "profile_initial.png"},
            "result": {"status": "success", "filename": "profile_initial.png"}
        },
        {
            "tool": "playwright_click",
            "args": {"element": "Edit Profile button", "ref": "button[data-testid='edit']"},
            "result": {"status": "success", "element": "Edit Profile button"}
        }
    ]
    
    for step in test_steps:
        print(f"  {step['tool']}: {json.dumps(step['result'])}")
    print()
    
    # Step 5: Store session memory
    print("STEP 5: Store session in memory (Claude-mem)")
    print("-" * 60)
    
    memory_result = {
        "status": "success",
        "tool": "add_episode",
        "name": "UserProfile Implementation",
        "episode_uuid": "ep-12345"
    }
    
    print(f"Session stored: {json.dumps(memory_result, indent=2)}")
    print()
    
    # Summary
    print("=" * 60)
    print("Workflow Complete!")
    print("=" * 60)
    print()
    print("Capabilities used:")
    print("  ✓ Codanna - Found similar code patterns")
    print("  ✓ Context7 - Retrieved React hooks documentation")
    print("  ✓ Graphiti - Stored implementation patterns")
    print("  ✓ Playwright - Tested in browser")
    print("  ✓ Claude-mem - Saved session for future reference")
    print()
    print("Benefits of unified server:")
    print("  - Single MCP connection instead of 5 separate ones")
    print("  - Shared context across capabilities")
    print("  - Progressive discovery reduces token usage")
    print()


if __name__ == "__main__":
    asyncio.run(multi_capability_workflow())
