# Contributing to Unified MCP Server

Thank you for your interest in contributing! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Adding a New Capability](#adding-a-new-capability)
- [Testing Guidelines](#testing-guidelines)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- Rust/Cargo (for Codanna)
- Git

### Setup Development Environment

```bash
# Clone repository with submodules
git clone --recursive https://github.com/yourusername/unified-mcp.git
cd unified-mcp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Initialize git submodules
git submodule update --init --recursive

# Run tests to verify setup
make test
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### 2. Make Changes

Follow the [Code Style](#code-style) guidelines.

### 3. Write Tests

All new code must include tests:
- Unit tests for core logic
- Integration tests for capability handlers
- E2E tests for full workflows

### 4. Run Quality Checks

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test

# All checks (format + lint + test)
make check
```

### 5. Commit Changes

```bash
git add .
git commit -m "feature: Add capability for X"
```

Commit message format:
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feature`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Adding a New Capability

Follow these steps to add a new capability to the unified MCP server:

### 1. Create Handler File

Create `handlers/my_capability.py`:

```python
"""
My Capability Handler
=====================

Description of what this capability does.

Maps unified-mcp tools to external service:
- my_tool_1 → external_operation_1
- my_tool_2 → external_operation_2
"""

import asyncio
from typing import Any, Dict
from core.capability_loader import CapabilityHandler


class MyCapabilityHandler(CapabilityHandler):
    """Handler for my capability tools."""

    def __init__(self, config: dict):
        """Initialize handler with config."""
        super().__init__(config)
        self.resource = None

    async def initialize(self) -> None:
        """Initialize the capability."""
        self.logger.info("Initializing MyCapability")
        # Setup connections, load resources, etc.

    async def get_tool_schema(self, tool_name: str) -> dict:
        """Get JSON schema for a tool."""
        schemas = {
            "my_tool": {
                "name": "my_tool",
                "description": "Tool description",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Parameter description",
                        }
                    },
                    "required": ["param1"],
                },
            },
        }

        if tool_name not in schemas:
            raise ValueError(f"Unknown tool: {tool_name}")

        return schemas[tool_name]

    async def execute(self, tool_name: str, arguments: dict) -> dict:
        """Execute a tool."""
        if tool_name == "my_tool":
            return await self._my_tool(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _my_tool(self, args: dict) -> dict:
        """Execute my_tool."""
        param1 = args["param1"]

        try:
            # Tool implementation
            result = await self._do_operation(param1)

            return {
                "status": "success",
                "tool": "my_tool",
                "result": result,
            }

        except Exception as e:
            self.logger.error(f"Error in my_tool: {e}")
            raise RuntimeError(f"MyCapability error: {e}")

    async def _do_operation(self, param: str) -> Any:
        """Helper method for tool operation."""
        # Implementation
        pass

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.resource:
            await self.resource.close()
        self.logger.info("MyCapability cleaned up")
```

### 2. Add to Catalog

Update `config/catalog.yaml`:

```yaml
capabilities:
  # ... existing capabilities ...

  my_capability:
    enabled: true
    type: my_capability
    source: capabilities/my_capability
    tools:
      - my_tool_1
      - my_tool_2
    lazy_load: true
    description: "Description of my capability"
```

### 3. Write Tests

Create `tests/integration/test_my_capability_handler.py`:

```python
"""
Integration Tests for My Capability Handler
============================================
"""

import pytest
from handlers.my_capability import MyCapabilityHandler


@pytest.fixture
def my_capability_config():
    """Configuration for my capability handler."""
    return {
        "type": "my_capability",
        "source": "capabilities/my_capability",
        "enabled": True,
    }


@pytest.fixture
async def my_capability_handler(my_capability_config):
    """Create and initialize handler."""
    handler = MyCapabilityHandler(my_capability_config)
    await handler.initialize()
    return handler


class TestMyCapabilityHandlerInitialization:
    """Tests for handler initialization."""

    @pytest.mark.asyncio
    async def test_handler_initializes_successfully(self, my_capability_handler):
        """Handler successfully initializes."""
        assert my_capability_handler is not None


class TestMyCapabilityToolSchemas:
    """Tests for tool schema definitions."""

    @pytest.mark.asyncio
    async def test_my_tool_schema(self, my_capability_handler):
        """my_tool has correct schema."""
        schema = await my_capability_handler.get_tool_schema("my_tool")

        assert schema["name"] == "my_tool"
        assert "param1" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["param1"]


class TestMyCapabilityToolExecution:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_my_tool_execution(self, my_capability_handler):
        """my_tool executes successfully."""
        result = await my_capability_handler.execute(
            "my_tool",
            {"param1": "test value"}
        )

        assert result["status"] == "success"
        assert result["tool"] == "my_tool"
```

### 4. Add Documentation

Create `capabilities/my_capability/README.md` with:
- Installation instructions
- Tool usage examples
- Configuration options
- Troubleshooting guide

### 5. Update Main README

Add your capability to the "Tools Available" section in `README.md`.

## Testing Guidelines

### Writing Good Tests

1. **Test one thing at a time**
```python
# Good
async def test_tool_returns_success_status():
    result = await handler.execute("my_tool", {"param": "value"})
    assert result["status"] == "success"

# Bad - tests multiple things
async def test_tool_execution():
    result = await handler.execute("my_tool", {"param": "value"})
    assert result["status"] == "success"
    assert result["tool"] == "my_tool"
    assert "result" in result
```

2. **Use descriptive test names**
```python
# Good
async def test_invalid_arguments_raises_type_error()

# Bad
async def test_error()
```

3. **Arrange, Act, Assert**
```python
async def test_my_tool():
    # Arrange
    handler = MyHandler(config)
    args = {"param": "value"}
    
    # Act
    result = await handler.execute("my_tool", args)
    
    # Assert
    assert result["status"] == "success"
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow  # For slow tests (API calls, etc.)
@pytest.mark.integration  # For integration tests
@pytest.mark.unit  # For unit tests
@pytest.mark.requires_openai  # For tests requiring OpenAI API
```

### Mocking External Services

Mock external services to make tests fast and reliable:

```python
from unittest.mock import AsyncMock, patch

async def test_tool_with_mocked_api():
    with patch.object(handler, "http_client") as mock_client:
        mock_client.post = AsyncMock(return_value={"result": "mocked"})
        
        result = await handler.execute("my_tool", {"param": "value"})
        
        assert result["status"] == "success"
        mock_client.post.assert_called_once()
```

## Code Style

### Python

We follow PEP 8 with Black formatting:

```bash
# Format code
black core handlers tests

# Check imports
isort core handlers tests

# Lint
flake8 core handlers --max-line-length=100
```

### Docstrings

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int) -> dict:
    """
    Brief description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this is raised
    """
    pass
```

### Type Hints

Use type hints for all function signatures:

```python
from typing import Dict, List, Optional

async def execute(self, tool_name: str, arguments: dict) -> Dict[str, Any]:
    """Execute a tool."""
    pass
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass (`make test`)
2. ✅ Code is formatted (`make format`)
3. ✅ No linting errors (`make lint`)
4. ✅ Documentation is updated
5. ✅ Commit messages follow convention

### PR Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] All tests passing

## Checklist

- [ ] Code formatted with black
- [ ] No linting errors
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
```

### Review Process

1. Automated tests run via GitHub Actions
2. Code review by maintainer(s)
3. Address review feedback
4. Approval and merge

### After Merge

- Delete your feature branch
- Pull latest main
- Continue with next feature!

## Questions?

Open an issue or reach out to maintainers!

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
