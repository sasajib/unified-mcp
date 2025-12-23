"""
Example 1: Progressive Discovery Pattern
=========================================

This example demonstrates the 3-step progressive discovery pattern that
reduces token usage from 10,000+ to 50-200 tokens.
"""

import asyncio
import json


async def progressive_discovery_example():
    """Demonstrate the progressive discovery pattern."""
    
    print("=" * 60)
    print("Progressive Discovery Pattern Example")
    print("=" * 60)
    print()
    
    # Step 1: Search for relevant tools (50 tokens)
    print("STEP 1: Search for relevant tools")
    print("-" * 60)
    
    search_query = "code search"
    print(f"Query: '{search_query}'")
    print()
    
    # This would return minimal tool previews
    tool_previews = [
        {
            "name": "search_code",
            "description": "Search codebase semantically",
            "capability": "code_understanding"
        },
        {
            "name": "find_symbol",
            "description": "Find symbol definitions",
            "capability": "code_understanding"
        }
    ]
    
    print("Results (50 tokens):")
    for tool in tool_previews:
        print(f"  - {tool['name']}: {tool['description']}")
    print()
    
    # Step 2: Get full schema for selected tool (200 tokens)
    print("STEP 2: Describe selected tool")
    print("-" * 60)
    
    selected_tool = "search_code"
    print(f"Selected tool: {selected_tool}")
    print()
    
    # This would return full JSON schema
    tool_schema = {
        "name": "search_code",
        "description": "Search codebase using semantic search powered by Codanna",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    }
    
    print("Full schema (200 tokens):")
    print(json.dumps(tool_schema, indent=2))
    print()
    
    # Step 3: Execute the tool
    print("STEP 3: Execute tool")
    print("-" * 60)
    
    tool_args = {
        "query": "authentication function",
        "limit": 5
    }
    
    print(f"Arguments: {json.dumps(tool_args, indent=2)}")
    print()
    
    # Mock results
    results = {
        "status": "success",
        "results": [
            {
                "file": "auth/login.py",
                "line": 45,
                "snippet": "def authenticate_user(username, password):"
            },
            {
                "file": "middleware/auth.py",
                "line": 12,
                "snippet": "def verify_token(token):"
            }
        ]
    }
    
    print("Results:")
    print(json.dumps(results, indent=2))
    print()
    
    # Summary
    print("=" * 60)
    print("Token Usage Summary")
    print("=" * 60)
    print()
    print("Traditional approach (all tools upfront):")
    print("  19 tools × 500 tokens/tool = 9,500 tokens")
    print()
    print("Progressive discovery:")
    print("  Step 1 (search):    50 tokens")
    print("  Step 2 (describe): 200 tokens")
    print("  Step 3 (execute):  300 tokens (variable)")
    print("  ─────────────────────────────")
    print("  Total:             550 tokens")
    print()
    print("Reduction: 94% (from 9,500 to 550)")
    print()


if __name__ == "__main__":
    asyncio.run(progressive_discovery_example())
