#!/bin/bash
# Test Runner Script for Unified MCP Server
# =========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Unified MCP Server Test Runner ===${NC}\n"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -q -r requirements-test.txt

# Parse command line arguments
TEST_TYPE="all"
COVERAGE=true
MARKERS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --e2e)
            TEST_TYPE="e2e"
            shift
            ;;
        --fast)
            MARKERS="-m 'not slow'"
            shift
            ;;
        --no-cov)
            COVERAGE=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--unit|--integration|--e2e] [--fast] [--no-cov]"
            exit 1
            ;;
    esac
done

# Run tests based on type
case $TEST_TYPE in
    unit)
        echo -e "${GREEN}Running unit tests...${NC}"
        TEST_PATH="tests/unit"
        ;;
    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        TEST_PATH="tests/integration"
        ;;
    e2e)
        echo -e "${GREEN}Running end-to-end tests...${NC}"
        TEST_PATH="tests/e2e"
        ;;
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        TEST_PATH="tests"
        ;;
esac

# Build pytest command
PYTEST_CMD="pytest $TEST_PATH"

if [ "$COVERAGE" = false ]; then
    PYTEST_CMD="$PYTEST_CMD --no-cov"
fi

if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD $MARKERS"
fi

# Run tests
echo -e "${YELLOW}Command: $PYTEST_CMD${NC}\n"
eval $PYTEST_CMD

# Check test result
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo -e "${YELLOW}Coverage report saved to htmlcov/index.html${NC}"
    fi
else
    echo -e "\n${RED}✗ Some tests failed${NC}"
    exit 1
fi
