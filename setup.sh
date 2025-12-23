#!/bin/bash
# Unified MCP Server - Setup Script
# ==================================

set -e  # Exit on error

echo "======================================"
echo "Unified MCP Server - Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then
    echo "ERROR: Python 3.12+ required"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Install test dependencies
echo ""
echo "Installing test dependencies..."
pip install -r requirements-test.txt

# Install Codanna (Rust - Phase 2)
echo ""
echo "Checking for Codanna..."
if command -v cargo &> /dev/null; then
    echo "Cargo found. You can install Codanna with:"
    echo "  cargo install codanna --all-features"
else
    echo "Cargo not found. Install Rust to use Codanna (Phase 2):"
    echo "  https://rustup.rs/"
fi

# Check Node.js (for Context7, Playwright - Phase 3)
echo ""
echo "Checking for Node.js..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "Node.js version: $node_version"
else
    echo "Node.js not found. Install Node.js for Context7/Playwright (Phase 3):"
    echo "  https://nodejs.org/"
fi

echo ""
echo "======================================"
echo "✅ Setup complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source .venv/bin/activate"
echo "  2. Run tests: pytest tests/ -v"
echo "  3. Start server: python server.py"
echo ""
echo "See README.md for more information."
