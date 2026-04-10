# Changelog

All notable changes to RealDataAgentBench are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Grok provider** (xAI) — `grok-3`, `grok-3-mini`, `grok-3-fast`, `grok-2-1212` via OpenAI-compatible API
- **Gemini provider** (Google) — `gemini-2.5-flash`, `gemini-2.5-pro` via OpenAI-compatible API
- **GPT-4.1 / GPT-5 family** — `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-5`, `gpt-5-mini`
- `realdataagentbench/harness/pricing.py` — single source of truth for all model costs (removes duplication between `providers.py` and `build_leaderboard.py`)
- `.env.example` — template for API key configuration

### Fixed
- `max_tokens` → `max_completion_tokens` in `OpenAIProvider` — required by GPT-5 and Gemini 2.5 Flash (reasoning models)
- Gemini alias updated from deprecated `gemini-2.0-flash` to `gemini-2.5-flash`
- `gemini-pro` alias updated from `gemini-1.5-pro` to `gemini-2.5-pro`

### Changed
- `.gitignore` — raw `outputs/*.json` files removed from git tracking; only `docs/results.json` is kept
- Cost table in `build_leaderboard.py` now imports from `harness/pricing.py` (no more duplication)

---

## [0.3.0] — 2026-04-09

### Added
- **Groq provider** — free `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768` via Groq API
- `--budget` flag on `dab run` — hard-caps API spend per run
- **Cost column** on leaderboard — $/task for every model
- SVG logo and 4 terminal-style screenshots in README

### Changed
- README rewrite: cleaner top section, "For Companies" cost-savings section, roadmap
- CONTRIBUTING.md rewrite with full provider + task + generator guides

---

## [0.2.0] — 2026-04-09

### Added
- **5 ML Engineering tasks** (`mod_001`–`mod_005`): data leakage detection, cross-validation, probability calibration, ensemble selection, nested CV
- 150+ offline tests (no API keys required), coverage threshold 80%
- Full internal package rename: `dataagentbench` → `realdataagentbench`
- Multi-model leaderboard: Claude Sonnet 4.6, GPT-4o, GPT-4o-mini, Claude Haiku 4.5

### Fixed
- Step budgets tuned per task (`eda_001` 8→20, `eda_003` 15→25, `feat_001` 12→20)
- Leaderboard merge conflict after rebase

---

## [0.1.0] — 2026-04-08

### Added
- **23 benchmark tasks** across 5 categories:
  - EDA (`eda_001`–`eda_003`): income distribution, patient records, e-commerce
  - Feature Engineering (`feat_001`–`feat_005`): encoding, scaling, interaction features, text, datetime
  - Modeling (`model_001`–`model_005`): logistic regression, random forest, XGBoost, linear regression, classification
  - Statistical Inference (`stat_001`–`stat_005`): t-tests, ANOVA, chi-square, correlation, SPC
- **18 seeded dataset generators** (reproducible, no external data files)
- **4-dimension scoring**: Correctness (40–45%), Code Quality (15–20%), Efficiency (15%), Statistical Validity (25–35%)
- **GitHub Pages leaderboard** with auto-rebuild CI on every push
- **Unified provider system**: Anthropic + OpenAI via `BaseProvider` abstraction
- Sandboxed code execution via `run_code` tool
- `dab` CLI: `list`, `inspect`, `run`, `score`, `models` commands
- MIT License

---

[Unreleased]: https://github.com/patibandlavenkatamanideep/RealDataAgentBench/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/patibandlavenkatamanideep/RealDataAgentBench/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/patibandlavenkatamanideep/RealDataAgentBench/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/patibandlavenkatamanideep/RealDataAgentBench/releases/tag/v0.1.0
