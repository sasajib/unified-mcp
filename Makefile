# Makefile for Unified MCP Server
# ================================

.PHONY: help install test test-unit test-integration test-e2e test-fast test-cov clean format lint docker

# Default target
help:
	@echo "Unified MCP Server - Development Commands"
	@echo "=========================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install all dependencies"
	@echo "  make install-dev      Install dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests with coverage"
	@echo "  make test-unit        Run only unit tests"
	@echo "  make test-integration Run only integration tests"
	@echo "  make test-e2e         Run only end-to-end tests"
	@echo "  make test-fast        Run tests excluding slow ones"
	@echo "  make test-cov         Run tests and open coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           Format code with black and isort"
	@echo "  make lint             Run flake8 and mypy"
	@echo "  make check            Run format, lint, and tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove cache and build files"
	@echo "  make clean-all        Remove cache, build files, and venv"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-run       Run Docker container"
	@echo ""

# Installation
install:
	python3 -m venv .venv || true
	.venv/bin/pip install -r requirements.txt

install-dev: install
	.venv/bin/pip install -r requirements-test.txt

# Testing
test:
	./run_tests.sh

test-unit:
	./run_tests.sh --unit

test-integration:
	./run_tests.sh --integration

test-e2e:
	./run_tests.sh --e2e

test-fast:
	./run_tests.sh --fast

test-cov: test
	@echo "Opening coverage report..."
	@which xdg-open > /dev/null && xdg-open htmlcov/index.html || open htmlcov/index.html

# Code quality
format:
	@echo "Formatting code..."
	.venv/bin/black core handlers tests
	.venv/bin/isort core handlers tests

lint:
	@echo "Running linters..."
	.venv/bin/flake8 core handlers --max-line-length=100 --ignore=E203,W503
	.venv/bin/mypy core handlers --ignore-missing-imports

check: format lint test

# Cleanup
clean:
	@echo "Cleaning cache and build files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true

clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf .venv

# Docker
docker-build:
	docker build -t unified-mcp:latest -f docker-compose.yml .

docker-run:
	docker-compose up -d
