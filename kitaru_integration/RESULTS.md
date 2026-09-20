# Results

Kitaru 0.26.0 local server, 2026-09-19. Scores from RDAB's `CompositeScorer`; the
`stat_validity` column was independently reproduced by the Kitaru evaluator and agreed
exactly on all 20 sessions.

## Baseline — 3 tasks × 3 models

| task | model | correctness | stat_validity | DAB | steps | tokens | cost |
|---|---|---|---|---|---|---|---|
| feat_001 | gemini-2.5-flash | 1.00 | 0.25 | 0.848 | 7 | 6,771 | $0.0016 |
| feat_003 | gemini-2.5-flash | 1.00 | 0.25 | 0.810 | 7 | 7,392 | $0.0018 |
| mod_004 | gemini-2.5-flash | 0.00 | 0.25 | 0.300 | 3 | 1,864 | $0.0003 |
| feat_001 | gpt-4o-mini | 0.00 | 0.25 | 0.236 | 60 | 138,981 | $0.0246 |
| feat_003 | gpt-4o-mini | 0.00 | 0.25 | 0.222 | 67 | 208,211 | $0.0338 |
| mod_004 | gpt-4o-mini | 1.00 | 0.50 | 0.790 | 12 | 15,964 | $0.0036 |
| feat_001 | claude-sonnet-4-6 | 1.00 | 0.625 | 0.856 | 19 | 30,528 | $0.1349 |
| feat_003 | claude-sonnet-4-6 | 1.00 | 0.50 | 0.891 | 28 | 52,751 | $0.2063 |
| mod_004 | claude-sonnet-4-6 | 1.00 | 0.75 | 0.875 | 9 | 19,676 | $0.1017 |

`llama-3.3-70b-versatile` was in the plan as the cheap model and could not run at all:
Groq has retired every Llama model in RDAB's registry (404, `model_not_found`).

Both `gpt-4o-mini` feature-engineering runs exhausted their step budget without producing
a final answer — 60 and 67 steps, 208k tokens — which is why correctness is 0.

## Candidate — statistical-validity prompt addendum

Applied to the four cases that were **correct but statistically weak** (correctness 1.00,
validity ≤ 0.50):

| task | model | stat_validity | correctness | tokens | cost |
|---|---|---|---|---|---|
| feat_001 | gemini-2.5-flash | 0.25 → **0.75** | 1.00 → 1.00 | 6,771 → 8,027 | $0.0016 → $0.0021 |
| feat_003 | gemini-2.5-flash | 0.25 → **1.00** | 1.00 → 1.00 | 7,392 → **5,190** | $0.0018 → **$0.0016** |
| feat_003 | claude-sonnet-4-6 | 0.50 → **1.00** | 1.00 → 1.00 | 52,751 → 206,502 | $0.2063 → $0.7409 |
| mod_004 | gpt-4o-mini | 0.50 → 0.50 | 1.00 → 1.00 | 15,964 → 45,896 | $0.0036 → $0.0097 |

**Mean stat_validity 0.375 → 0.812 (+0.44). Correctness held at 1.00 in every case.**

### What the averages hide

- **gemini-2.5-flash on feat_003 reached 1.00 while using fewer tokens** (7,392 → 5,190).
  More rigour did not have to cost more.
- **claude-sonnet-4-6 quadrupled its token use** (52.8k → 206.5k, $0.21 → $0.74) and hit
  `max_steps=30`. Its validity reached 1.00 but its DAB score *fell*, 0.891 → 0.833,
  because efficiency collapsed. An earlier attempt at a $0.50 cap was killed mid-run by
  the budget guard, scoring correctness 0.00 — a cap, not a model failure.
- **gpt-4o-mini gained nothing on mod_004** (0.50 → 0.50) while spending 2.9× the tokens.

So "this prompt improves statistical validity" is true on average and wrong in two of four
cases if you care about cost, and one of those two is a regression on the composite score.

## Replay economics

The brief expected "tokens saved by replaying from a checkpoint". That number does not
exist here, for two measured reasons:

1. Kitaru replays re-run an agent **from the top** — the docs state there is no mid-run cut
   point — so model calls are re-executed, not skipped.
2. What replay does cache is *tool results* (`--tool-policy history`). RDAB's tools are
   local sandboxed `run_code` calls, which cost no tokens. Pinning them buys determinism,
   not money.

The candidate re-runs therefore cost full price: **$1.29 for 5 runs**, versus $0.51 for the
15 baseline runs.
