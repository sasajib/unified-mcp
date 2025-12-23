# Unified Dynamic MCP Server

**Single MCP server with progressive discovery for 96-160x token reduction**

Consolidates code understanding (Codanna), documentation (Context7), browser automation (Playwright), memory (Claude-mem), and knowledge graph (Graphiti+LadybugDB) into one unified server.

## Features

✨ **Progressive Discovery** - 3-step pattern reduces tokens from 10,000+ to 50-200
🔧 **Dynamic Tool Loading** - Lazy load capabilities only when needed
🎯 **5 Integrated Capabilities** - Code, docs, browser, memory, knowledge graph
🚀 **Git Submodules** - Auto-update with `git submodule update --remote`
⚡ **Fast** - Sub-10ms symbol lookup (Codanna), embedded LadybugDB (no Docker)

## Quick Start

```bash
# Clone with submodules
git clone --recursive https://github.com/yourusername/unified-mcp.git
cd unified-mcp

# Install dependencies (using uv - recommended)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start server (with uv)
uvx --directory . -p 3.12 server.py

# Or with python
python server.py
```

**Add to Claude Code:**
```bash
claude mcp add unified-mcp
# Command: uvx
# Arguments: --directory /path/to/unified-mcp -p 3.12 server.py
```

## Progressive Discovery Pattern

Traditional approach: Load all 20 tools upfront = **10,000 tokens**

Our approach:
1. **Search** (`search_tools`) → Find relevant tools → **~50 tokens**
2. **Describe** (`describe_tools`) → Get full schemas → **~200 tokens/tool**
3. **Execute** (`execute_tool`) → Run the tool → **Variable**

**Result: 98% token reduction** 🎉

## Architecture

```
Unified MCP Server
├── Progressive Discovery Engine
├── Dynamic Tool Registry
├── 5 Capability Modules
│   ├── Codanna (code understanding)
│   ├── Context7 (documentation)
│   ├── Playwright (browser automation)
│   ├── Claude-mem (memory)
│   └── Graphiti+LadybugDB (knowledge graph)
```

## Installation

### Requirements

- **Python 3.12+** (for LadybugDB)
- **Rust/Cargo** (for Codanna) - [Install Rust](https://rustup.rs/)
- **Node.js 18+** (for Context7/Playwright) - [Install Node](https://nodejs.org/)

### Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Codanna (code understanding)
cargo install codanna --all-features

# Git submodules (Phase 2+)
git submodule update --init --recursive
cd capabilities/context7 && npm install
cd ../playwright-mcp && npm install
cd ../claude-mem && npm install
```

## Usage

### Start Server

```bash
python server.py
```

Server runs on stdio (MCP protocol).

### Configure with Claude Code

**Option 1: Using `claude mcp add` (Recommended)**

```bash
# Add the unified MCP server
claude mcp add unified-mcp

# When prompted, use this configuration:
# Command: uvx
# Arguments: --directory /absolute/path/to/unified-mcp -p 3.12 server.py
```

**Option 2: Manual Configuration**

Add to your MCP settings file (`~/.config/claude/mcp_settings.json`):

```json
{
  "mcpServers": {
    "unified-mcp": {
      "command": "uvx",
      "args": [
        "--directory",
        "/absolute/path/to/unified-mcp",
        "-p",
        "3.12",
        "server.py"
      ],
      "env": {
        "CODANNA_INDEX_DIR": "${workspaceFolder}/.codanna",
        "CLAUDE_MEM_API_URL": "http://localhost:37777",
        "GRAPHITI_ENABLED": "true",
        "GOOGLE_API_KEY": "your-gemini-api-key-here"
      }
    }
  }
}
```

**With Graphiti + Google Gemini (Full Configuration):**

```json
{
  "mcpServers": {
    "unified-mcp": {
      "command": "uvx",
      "args": [
        "--directory",
        "/absolute/path/to/unified-mcp",
        "-p",
        "3.12",
        "server.py"
      ],
      "env": {
        "CODANNA_INDEX_DIR": "${workspaceFolder}/.codanna",
        "CLAUDE_MEM_API_URL": "http://localhost:37777",
        "GRAPHITI_ENABLED": "true",
        "GRAPHITI_LLM_PROVIDER": "google_ai",
        "GRAPHITI_EMBEDDER_PROVIDER": "google_ai",
        "GOOGLE_API_KEY": "your-gemini-api-key-here",
        "GRAPHITI_LLM_MODEL": "gemini-1.5-pro",
        "GRAPHITI_EMBEDDER_MODEL": "text-embedding-004"
      }
    }
  }
}
```

**Environment Variables:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CODANNA_INDEX_DIR` | No | `.codanna` | Codanna index directory |
| `CLAUDE_MEM_API_URL` | No | `http://localhost:37777` | Claude-mem API endpoint |
| `GRAPHITI_ENABLED` | No | `false` | Enable Graphiti knowledge graph |
| `GRAPHITI_LLM_PROVIDER` | No | `openai` | LLM provider: `openai`, `anthropic`, `azure_openai`, `ollama`, `google_ai` |
| `GRAPHITI_EMBEDDER_PROVIDER` | No | `openai` | Embedder: `openai`, `voyage_ai`, `azure_openai`, `ollama`, `google_ai` |
| `GOOGLE_API_KEY` | If using Gemini | - | Google AI API key for Gemini |
| `OPENAI_API_KEY` | If using OpenAI | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | If using Claude | - | Anthropic API key |

**Restart Claude Code** to load the server.

**Verify it's working:**
- Ask Claude: "What tools do you have available?"
- You should see tools like `search_tools`, `describe_tools`, `execute_tool`, etc.

### Configuration

Edit `config/catalog.yaml`:

```yaml
capabilities:
  code_understanding:
    enabled: true  # Toggle capabilities
    tools: [search_code, get_call_graph, ...]
```

### Tools Available

**Progressive Discovery** (Meta-tools):
- `search_tools(query)` - Find relevant tools
- `describe_tools([names])` - Get full schemas
- `execute_tool(name, args)` - Run a tool

**Capability Management**:
- `list_capabilities()` - See all capabilities
- `enable_capability(name)` - Enable at runtime
- `disable_capability(name)` - Disable at runtime

**Code Understanding** (Codanna - Phase 2):
- `search_code` - Semantic code search
- `get_call_graph` - Function relationships
- `find_symbol` - Symbol lookup (sub-10ms)
- `find_implementations` - Find implementations

**Documentation** (Context7 - Phase 3):
- `resolve_library_id` - Resolve library name
- `get_library_docs` - Fetch documentation

**Browser Automation** (Playwright - Phase 3):
- `playwright_navigate` - Navigate to URL
- `playwright_screenshot` - Take screenshot
- `playwright_click` - Click element
- `playwright_fill` - Fill form field
- `playwright_evaluate` - Execute JavaScript

**Memory** (Claude-mem - Phase 4):
- `mem_search` - Search observations
- `mem_get_observation` - Get by ID
- `mem_recent_context` - Recent sessions
- `mem_timeline` - Timeline view

**Knowledge Graph** (Graphiti - Phase 4):
- `store_insight` - Store knowledge
- `search_insights` - Search insights
- `query_graph` - Cypher queries
- `add_episode` - Add episode

## Development

### Run Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=. --cov-report=term-missing

# Skip slow tests
pytest tests/ -m "not slow"
```

### Project Structure

```
unified-mcp/
├── server.py              # Main MCP server
├── config/
│   └── catalog.yaml       # Capability configuration
├── core/
│   ├── dynamic_registry.py
│   ├── progressive_discovery.py
│   └── capability_loader.py
├── handlers/             # Capability handlers
├── capabilities/         # Git submodules
├── tests/               # Comprehensive test suite
└── docs/                # Documentation
```

## Implementation Status

- ✅ **Phase 1**: Foundation (Dynamic registry, progressive discovery)
- ✅ **Phase 2**: Codanna integration (4 code understanding tools)
- ✅ **Phase 3**: Context7 + Playwright (7 tools: docs + browser automation)
- ✅ **Phase 4**: Claude-mem + Graphiti (8 tools: memory + knowledge graph)
- ✅ **Phase 5**: Comprehensive testing (Unit + Integration + E2E, 80%+ coverage, CI/CD)
- ✅ **Phase 6**: Documentation (Complete)

## License

Apache 2.0

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [Docker MCP Gateway](https://github.com/docker/mcp-gateway)
- [Codanna](https://github.com/bartolli/codanna)
- [Context7](https://github.com/upstash/context7)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
- [Claude-mem](https://github.com/thedotmack/claude-mem)
