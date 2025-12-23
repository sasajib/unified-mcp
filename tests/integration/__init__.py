"""
Integration Tests
==================

Integration tests for unified-mcp capabilities.

These tests require external dependencies:
- Codanna: cargo install codanna --all-features
- Context7: npm install -g @upstash/context7-mcp
- Playwright: npm install -g playwright-mcp

Tests are marked with:
- @pytest.mark.slow - Tests that take >1s
- @pytest.mark.skipif - Tests that require specific dependencies

Run all tests: pytest tests/integration/ -v
Skip slow tests: pytest tests/integration/ -m "not slow"
"""
