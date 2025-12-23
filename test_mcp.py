#!/usr/bin/env python3
"""Test MCP server by sending a list_tools request."""

import asyncio
import json
import subprocess
import sys


async def test_mcp_server():
    """Test the MCP server's list_tools response."""

    # Start the server process
    proc = await asyncio.create_subprocess_exec(
        "uv", "run", "server.py",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Send MCP initialize request
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }

    # Send request
    proc.stdin.write(json.dumps(initialize_request).encode() + b'\n')
    await proc.stdin.drain()

    # Read response
    response = await proc.stdout.readline()
    print("Initialize response:")
    print(response.decode())

    # Send list_tools request
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    proc.stdin.write(json.dumps(list_tools_request).encode() + b'\n')
    await proc.stdin.drain()

    # Read response
    response = await proc.stdout.readline()
    print("\nList tools response:")
    try:
        data = json.loads(response.decode())
        print(json.dumps(data, indent=2))

        if "result" in data and "tools" in data["result"]:
            print(f"\n✅ Found {len(data['result']['tools'])} tools!")
            for tool in data['result']['tools']:
                print(f"  - {tool['name']}: {tool['description'][:60]}...")
        else:
            print("❌ No tools found in response")
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        print(response.decode())

    # Cleanup
    proc.terminate()
    await proc.wait()


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
