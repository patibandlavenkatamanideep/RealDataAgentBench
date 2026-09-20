# Can this leaderboard still be reproduced?

`docs/results.json` holds 500 recorded runs. A row is only evidence if the same command
still produces a run today. Two things break that without anyone touching this repo:
a provider retires a model, or a provider SDK changes a parameter the harness still sends.

Run the audit yourself — it uses only free list-models endpoints, so it costs nothing:

```bash
python scripts/audit_model_availability.py
```

## Result, 2026-09-20

The audit reports against whatever harness code it is run with, so it gives two answers.

| | as found on `main` | with the SDK fix on `kitaru-integration` |
|---|---|---|
| Reproducible | 300 (60%) | **379 (76%)** |
| Blocked | **118 (24%)** | 39 (8%) |
| Unchecked (no key here, or a local runtime) | 82 (16%) | 82 (16%) |

A one-line change restores 79 of the 118 blocked runs. The remaining 39 need a decision
about the registry, not a code fix — the model is genuinely gone.

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
still works and the other three do not.

Fixed on the `kitaru-integration` branch by asking the installed SDK whether the parameter
exists instead of maintaining a version table:

```python
self._sdk_accepts_temperature = "temperature" in inspect.signature(
    self.client.messages.create
).parameters
```

With that in place the audit reports these 79 runs as reproducible again.

### Unchecked — 82 runs

`gemma4` (43) needs a local Ollama daemon; `grok-3-mini` (39) needs an xAI key. Neither is
configured here, so they are reported as unchecked rather than counted either way.

## What this means

Nothing in this repository changed. 24% of the leaderboard stopped being reproducible
because the ecosystem moved underneath it — and nothing in the harness noticed or recorded
that. A benchmark that reports a score without recording whether that score can still be
obtained is reporting history, not a measurement.

Both mitigations are now implemented on the `kitaru-integration` branch:

1. **`scripts/audit_model_availability.py --check`** exits non-zero when a model with
   recorded runs can no longer be called, and `.github/workflows/model-availability.yml`
   runs it weekly and on any change to the provider registry. Providers without a secret
   are reported as unchecked and never fail the build.
2. **Every run records the client library that served it.** `_build_result` now stores
   `environment: {"sdk": "anthropic", "sdk_version": "1.7.0"}`, so an SDK-side break is
   visible in the result JSON rather than only at the next execution.
