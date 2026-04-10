.PHONY: install test test-cov lint clean leaderboard run-all help

PYTHON  := python3
PACKAGE := realdataagentbench

# ── Setup ─────────────────────────────────────────────────────────────────────

install:          ## Install the package in editable mode with dev dependencies
	$(PYTHON) -m pip install -e ".[dev]"

# ── Testing ───────────────────────────────────────────────────────────────────

test:             ## Run the test suite (offline, no API keys needed)
	$(PYTHON) -m pytest tests/ -v

test-cov:         ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ -v --cov=$(PACKAGE) --cov-report=term-missing --cov-fail-under=80

# ── Code quality ──────────────────────────────────────────────────────────────

lint:             ## Run ruff linter
	$(PYTHON) -m ruff check $(PACKAGE) scripts/

fmt:              ## Auto-format with ruff
	$(PYTHON) -m ruff format $(PACKAGE) scripts/

# ── Leaderboard ───────────────────────────────────────────────────────────────

leaderboard:      ## Rebuild docs/results.json from outputs/*.json
	$(PYTHON) scripts/build_leaderboard.py

# ── Benchmark runs ────────────────────────────────────────────────────────────

run-all:          ## Run all 23 tasks with the default model (set MODEL=gpt-4o etc.)
	MODEL ?= claude-sonnet-4-6; \
	$(PYTHON) -m $(PACKAGE).cli run --model $${MODEL:-claude-sonnet-4-6}

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:            ## Remove build artifacts, caches, and coverage reports
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .coverage htmlcov/ .pytest_cache/ .ruff_cache/

# ── Help ──────────────────────────────────────────────────────────────────────

help:             ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
