# DataAgentBench

[![CI](https://github.com/patibandlavenkatamanideep/dataagentbench/actions/workflows/ci.yml/badge.svg)](https://github.com/patibandlavenkatamanideep/dataagentbench/actions)

**A benchmark for evaluating LLM agents on data science tasks.**

DataAgentBench (DAB) measures how well LLM agents perform real data science work — exploratory data analysis, missing data handling, statistical validity, and confounding detection — using statistically rigorous, multi-dimensional scoring.

## Quickstart

```bash
pip install -e ".[dev]"

# List all tasks
dab list

# Inspect a task
dab inspect eda_001

# Dry-run (no API call)
dab run eda_001 --dry-run

# Run for real (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
dab run eda_001

# Score a result file
dab score outputs/eda_001_<timestamp>.json
```

## Tasks

| ID | Title | Difficulty |
|----|-------|-----------|
| eda_001 | Income Distribution Analysis | Easy |
| eda_002 | Patient Records — Missing Data & Outlier Audit | Medium |
| eda_003 | E-Commerce Confounding Variable Detection | Hard |

## Scoring

Each task is scored across four dimensions:

| Dimension | What it measures |
|-----------|-----------------|
| **Correctness** | Ground truth match (skewness direction, missing columns, etc.) |
| **Code Quality** | Vectorized ops, descriptive names, no raw loops |
| **Efficiency** | Tokens and steps used vs. budget |
| **Stat Validity** | Uncertainty reporting, appropriate methods, interpretation |

The final **DAB Score** is a weighted average of the four dimensions (weights defined per task).

## Project Structure

```
dataagentbench/
├── core/           # Pydantic schema + task registry
├── datasets/       # Seeded dataset generators
├── harness/        # Agent loop, tools, tracer, runner
├── scoring/        # Four-dimension scoring engine
└── cli.py          # dab CLI
tasks/eda/          # Task YAML definitions
tests/              # Full offline test suite
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
