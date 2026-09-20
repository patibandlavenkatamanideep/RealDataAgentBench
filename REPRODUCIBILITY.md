# Can this leaderboard still be reproduced?

`docs/results.json` holds 500 recorded runs. A row is only evidence if the same command
still produces a run today. Two things break that without anyone touching this repo:
a provider retires a model, or a provider SDK changes a parameter the harness still sends.

Run the audit yourself — it uses only free list-models endpoints, so it costs nothing:

```bash
python scripts/audit_model_availability.py
```

## Result, 2026-09-20

| | runs | share |
|---|---|---|
| Reproducible today | 300 | 60% |
| **Blocked** | **118** | **24%** |
| Unchecked (no key here, or a local runtime) | 82 | 16% |

### Blocked: retired at the provider — 39 runs

`llama-3.3-70b-versatile` returns `404 model_not_found` from Groq. Every one of the seven
models in `GROQ_MODELS` is gone; only that one has recorded runs.

```
Error code: 404 - {'error': {'message': 'The model `llama-3.3-70b-versatile` does not
exist or you do not have access to it.', 'code': 'model_not_found'}}
```

### Blocked: the model is live, the SDK is not — 79 runs

`claude-haiku-4-5-20251001` (33), `claude-opus-4-6` (23) and `claude-sonnet-4-6` (23) are
all still served by Anthropic. They fail anyway:

```
Messages.create() got an unexpected keyword argument 'temperature'
```

`anthropic>=1.0` removed `temperature` from `messages.create()`. The harness only skipped
it for the models in `NO_SAMPLING_PARAM_MODELS`, which is why `claude-opus-4-8` (43 runs)
still works and the other three do not. Fixed on the `kitaru-integration` branch by asking
the installed SDK whether the parameter exists rather than keeping a version table.

### Unchecked — 82 runs

`gemma4` (43) needs a local Ollama daemon; `grok-3-mini` (39) needs an xAI key. Neither is
configured here, so they are reported as unchecked rather than counted either way.

## What this means

Nothing in this repository changed. 24% of the leaderboard stopped being reproducible
because the ecosystem moved underneath it — and nothing in the harness noticed or recorded
that. A benchmark that reports a score without recording whether that score can still be
obtained is reporting history, not a measurement.

Two cheap mitigations, neither implemented yet:

1. Run this audit in CI and fail when a model with recorded runs disappears.
2. Record the resolved provider SDK version alongside each run, so an SDK-side break is
   visible in the data rather than only at the next execution.
