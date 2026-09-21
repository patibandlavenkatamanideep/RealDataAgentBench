# Draft X thread — benchmark rot (7 posts)

Every number measured in this repo on 2026-09-20 with
`python scripts/audit_model_availability.py`. Written for: people who publish or rely on
LLM benchmark numbers.

---

**1/**
I audited my own LLM benchmark leaderboard — 500 recorded runs — against the providers'
live model lists.

24% of it can't be reproduced today.

I changed nothing. The ecosystem moved.

---

**2/**
39 runs: `llama-3.3-70b-versatile` is gone.

```
404 - The model `llama-3.3-70b-versatile`
does not exist or you do not have access
```

Groq has retired every Llama model my registry knows about. Those rows are now history,
not measurements.

---

**3/**
79 runs: the model is alive, my harness can't call it.

```
Messages.create() got an unexpected
keyword argument 'temperature'
```

`anthropic>=1.0` removed `temperature`. My code still sent it. 0 steps, 0 tokens, instant
failure on 3 Claude models.

---

**4/**
The quiet part: `claude-opus-4-8` still works.

Only because it was already on a hand-maintained "doesn't take sampling params" list. The
other three weren't.

My workaround was a version table. Version tables expire.

---

**5/**
Fix that doesn't expire — ask the installed SDK what it accepts:

```python
self._sdk_accepts_temperature = "temperature" in inspect.signature(
    self.client.messages.create
).parameters
```

One line. Restores 79 runs. No list to maintain.

---

**6/**
The part I find uncomfortable:

Nothing in my harness noticed. No warning, no recorded SDK version, no check. The
leaderboard still renders 500 rows as if they all mean the same thing.

A score without "can I still get this score" is not a measurement.

---

**7/**
Two cheap fixes I'd want in any benchmark:

1. Audit model availability in CI; fail when a model with recorded runs disappears
2. Record the provider SDK version with each run, so SDK breaks show up in the data

Audit script + full report: [link]

---

## Notes before posting

- Post 1's "24%" = 118 of 500 runs, measured against `main` as found. Another 16%
  (82 runs: gemma4 via Ollama, grok-3-mini via xAI) is *unchecked* here, not broken —
  don't round it into the 24%.
- After the one-line fix in post 5, the audit reports 39 blocked (8%) and 379 reproducible
  (76%). If you post the fix, post that number with it.
- The `claude-opus-4-8` claim in post 4 is from the registry, not a live run today; it was
  excluded from the temperature path by `NO_SAMPLING_PARAM_MODELS`.
- Post 5's snippet is on the `kitaru-integration` branch, not `main`, at the time of writing.
