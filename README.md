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
# Clone with submodules (Phase 2+)
git clone --recursive <your-repo>
cd unified-mcp

# Setup (creates venv, installs deps)
./setup.sh

# Activate virtual environment
source .venv/bin/activate

# Run tests
pytest tests/ -v

# Start server
python server.py
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
- ⏳ **Phase 2**: Codanna integration
- ⏳ **Phase 3**: Context7 + Playwright
- ⏳ **Phase 4**: Claude-mem + Graphiti
- ⏳ **Phase 5**: Comprehensive testing
- ⏳ **Phase 6**: Documentation

## License

Apache 2.0

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [Docker MCP Gateway](https://github.com/docker/mcp-gateway)
- [Codanna](https://github.com/bartolli/codanna)
- [Context7](https://github.com/upstash/context7)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
- [Claude-mem](https://github.com/thedotmack/claude-mem)
