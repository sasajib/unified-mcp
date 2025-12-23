# Usage Examples

This directory contains examples demonstrating different features and workflows of the Unified MCP Server.

## Examples

### 01_progressive_discovery.py

Demonstrates the 3-step progressive discovery pattern that achieves 96-160x token reduction:
1. **Search**: Find relevant tools (~50 tokens)
2. **Describe**: Get full schemas (~200 tokens/tool)
3. **Execute**: Run the tool (variable tokens)

**Run it:**
```bash
python examples/01_progressive_discovery.py
```

**Learn:**
- How progressive discovery reduces tokens from 10,000+ to 50-200
- The search → describe → execute flow
- Token usage comparison with traditional approach

### 02_multi_capability.py

Shows how to use multiple capabilities together in a realistic development workflow.

**Run it:**
```bash
python examples/02_multi_capability.py
```

**Demonstrates:**
- Using Codanna to search existing code
- Fetching documentation with Context7
- Storing insights in Graphiti knowledge graph
- Testing with Playwright browser automation
- Saving session context with Claude-mem

## Running Examples

All examples are standalone Python scripts:

```bash
# Run an example
python examples/01_progressive_discovery.py

# Or activate venv first
source .venv/bin/activate
python examples/01_progressive_discovery.py
```

## Creating Your Own Examples

To create a new example:

1. Create a new file: `examples/03_my_example.py`
2. Add a docstring explaining what it demonstrates
3. Include clear step-by-step output
4. Add it to this README

Example template:

```python
"""
Example N: Your Example Title
==============================

Brief description of what this example demonstrates.
"""

import asyncio
import json


async def my_example():
    """Demonstrate XYZ."""
    
    print("=" * 60)
    print("My Example Title")
    print("=" * 60)
    print()
    
    # Your example code here
    
    print("Summary:")
    print("  - Key takeaway 1")
    print("  - Key takeaway 2")
    print()


if __name__ == "__main__":
    asyncio.run(my_example())
```

## More Resources

- [Architecture Documentation](../ARCHITECTURE.md) - System design and internals
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute
- [README](../README.md) - Main project documentation
- Individual capability docs in `capabilities/*/README.md`

## Need Help?

- Open an issue on GitHub
- Check the troubleshooting sections in capability READMEs
- Review the test files for more usage examples
