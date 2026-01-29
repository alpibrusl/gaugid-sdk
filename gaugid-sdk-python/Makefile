.PHONY: help install install-dev test test-cov lint format type-check security clean coverage-report

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package
	pip install -e .

install-dev: ## Install package with dev dependencies
	pip install -e ".[dev]"
	@if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then \
		echo "Installing pre-commit hooks..."; \
		pre-commit install || echo "⚠️  Pre-commit hooks installation failed (non-fatal)"; \
	else \
		echo "⚠️  Skipping pre-commit hooks (not in a git repository)"; \
	fi

install-dev-local: ## Install package with local a2p SDK (for development)
	@echo "Installing local a2p SDK from ../../a2p..."
	@if [ -f "../../a2p/packages/sdk/python/pyproject.toml" ]; then \
		echo "Found a2p SDK at: ../../a2p/packages/sdk/python"; \
		pip install -e ../../a2p/packages/sdk/python; \
	elif [ -d "../../a2p/packages/sdk-python" ] && [ -f "../../a2p/packages/sdk-python/pyproject.toml" ]; then \
		echo "Found a2p SDK at: ../../a2p/packages/sdk-python"; \
		pip install -e ../../a2p/packages/sdk-python; \
	elif [ -d "../../a2p" ] && [ -f "../../a2p/pyproject.toml" ]; then \
		echo "Found a2p SDK at: ../../a2p"; \
		pip install -e ../../a2p; \
	else \
		echo "⚠️  a2p SDK not found at ../../a2p. Cannot proceed without it."; \
		exit 1; \
	fi
	@echo "Installing gaugid SDK core dependencies..."
	pip install httpx>=0.25.0 pydantic>=2.0.0 cryptography>=41.0.0
	@echo "Installing gaugid SDK (editable mode, no deps)..."
	pip install -e . --no-deps
	@echo "Installing dev dependencies..."
	pip install pytest>=8.0.0 pytest-asyncio>=0.23.0 pytest-cov>=4.1.0 pytest-mock>=3.12.0 mypy>=1.8.0 ruff>=0.1.0 black>=24.0.0 pre-commit>=3.6.0 types-requests>=2.31.0
	@if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then \
		echo "Installing pre-commit hooks..."; \
		pre-commit install || echo "⚠️  Pre-commit hooks installation failed (non-fatal)"; \
	else \
		echo "⚠️  Skipping pre-commit hooks (not in a git repository)"; \
	fi

test: ## Run tests
	pytest --tb=short -v

test-cov: ## Run tests with coverage report
	pytest \
		--cov=gaugid \
		--cov-report=html \
		--cov-report=term-missing \
		--cov-report=xml \
		--cov-fail-under=80 \
		--tb=short \
		-v

coverage-report: test-cov ## Generate and open coverage report
	@echo "Coverage report generated in htmlcov/index.html"
	@python -m webbrowser htmlcov/index.html || echo "Open htmlcov/index.html in your browser"

check-coverage: ## Run coverage analysis script (works without a2p-sdk)
	@bash check_coverage.sh

lint: ## Run linters (ruff, black check)
	ruff check src/ tests/
	ruff format --check src/ tests/
	black --check src/ tests/

format: ## Format code (ruff format, black)
	ruff format src/ tests/
	black src/ tests/

type-check: ## Run type checker (mypy)
	mypy src/gaugid

security: ## Run security scan (bandit)
	bandit -r src/ -ll -f json -o bandit-report.json

pre-commit: ## Run all pre-commit hooks
	pre-commit run --all-files

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf bandit-report.json

ci: lint type-check test-cov security ## Run all CI checks locally
