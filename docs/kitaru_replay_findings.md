# Kitaru Replay Lab — findings

A narrow experiment: wrap one RDAB execution path so a benchmark run can be replayed
instead of re-paid for, and report what Kitaru actually contributes.

Run it yourself, offline and free:

```bash
python scripts/kitaru_replay_lab.py \
  --tasks feat_001,feat_003 --model gemini-2.5-flash --runs 1 \
  --out artifacts/kitaru_replay/
```

Environment: Kitaru 0.26.0 (local server, Podman via the Docker CLI), macOS arm64,
Python 3.13, 2026-09-20.

## Summary

| Question | Finding |
|---|---|
| Can RDAB runs be checkpointed? | Yes, but not by Kitaru. The path splits cleanly into 5 serializable steps; Kitaru has no checkpoint API, so the lab implements them directly |
| Can model calls be replayed safely? | Yes. Replaying a recorded trace reproduced `dab_score` to the digit on every case, at $0 |
| Did replay preserve functional result? | Exactly. feat_001 0.848 → 0.848, feat_003 0.810 → 0.810; correctness, code quality, efficiency and stat validity all identical |
| What integration friction appeared? | 14 items in `kitaru_integration/FRICTION.md`. The blocking one: no `@flow`/`@checkpoint`, and replay cannot resume mid-run |
| Best next step | Ship the recorded-provider path as a first-class RDAB mode; revisit Kitaru replay if a generic (non-framework) agent adapter appears |

## 1. What execution path was wrapped?

The single-task path, `Runner.run_task` → `Agent.run` → `<Provider>.run` → `CompositeScorer`,
for one model and a two-task subset (`feat_001`, `feat_003`). Nothing else in the benchmark
was touched: `dab run` behaves exactly as before, and the new module is imported by nothing
in the normal path.

## 2. Which steps became checkpoints?

| # | step | output | deterministic? |
|---|---|---|---|
| 1 | `load_benchmark_case` | task id, category, dataset shape, seed | yes — generator + seed |
| 2 | `build_model_input` | prompt length + SHA-256 | yes |
| 3 | `run_model` | full trace: steps, tool calls, tokens | **no — the expensive step** |
| 4 | `score_output` | the four dimensions + DAB score | yes — pure functions |
| 5 | `write_result_row` | artifact path and size | yes |

Step 3 is the only one that costs money, which is what makes the boundary worth drawing
there.

## 3. What replayed successfully?

Both tasks, end to end, from recorded traces with no API key present:

```
feat_001   replay  dab=0.848 validity=0.25 tokens=  6771 0.05s
feat_003   replay  dab=0.810 validity=0.25 tokens=  7392 0.05s
model tokens served from recordings: 14,163 ($0.0034 not spent)
```

## 4. What changed between first run and replay?

Nothing in the result; a great deal in the cost of getting it.

| | live | replay | |
|---|---|---|---|
| dab_score, feat_001 | 0.848 | 0.848 | identical |
| dab_score, feat_003 | 0.810 | 0.810 | identical |
| wall time | 19s / 17s | 0.05s / 0.05s | ~350× faster |
| API cost | $0.0034 | $0.00 | — |
| API key required | yes | **no** | runs in CI |

The scores are identical because replay serves the recorded assistant turns and tool
results; only the scoring code re-executes. That is the property worth having — it isolates
a scorer change from model drift.

## 5. Did Kitaru avoid re-running expensive/model steps?

**No, and it is not designed to.** Two measured reasons:

1. Kitaru's replay re-runs the agent from the top. From its own docs: *"replays re-run the
   agent from the top. There is no partial, mid-run cut point."*
2. What Kitaru's replay does cache is **tool results**, through
   `--tool-policy '{"default":{"type":"history",...}}'`. RDAB's tools are local sandboxed
   `run_code` calls that cost no tokens, so pinning them buys determinism, not money.

The saving in section 4 comes from the lab's own recorded provider, not from Kitaru. Said
plainly: for RDAB today, **Kitaru is an evidence store and evaluator, not a cost saver**.

We also could not run a Kitaru replay against RDAB at all. Registering the agent and
calling `kitaru replay create` dispatches the job, then fails:

```
Agent process exited with code 1.
stdout tail: Running {task_id} (model={model}, dry_run=False, runs=1)
```

The command is executed verbatim; the real contract (`KITARU_TASK_INPUTS`,
`KITARU_REPLAY_ID` in the environment) is in `kitaru/worker/handlers/agent.py`, not in the
docs. Implementing it means writing an adapter — the shipped PydanticAI equivalent is 1,084
lines.

## 6. Where does Kitaru fit RDAB well?

- **Evidence store.** 20 RDAB runs imported as sessions, with per-step `llm_call` /
  `tool_call` nodes, token usage and cost derived automatically.
- **Evaluators.** RDAB's `StatValidityScorer` registered as a Kitaru evaluator agreed with
  `dab score` on all 20 sessions, and reports *which* of its four checks failed —
  `uncertainty=0.0 method=False interpretation=False` — which is what made a targeted
  prompt fix possible.
- **Cohorts.** The four correct-but-weak sessions froze into an immutable cohort version,
  so a fix is measured against a fixed population rather than a moving one.
- **Local-first.** Everything above ran against a local server; the worker executes your
  code, so no keys or prompts left the machine.

## 7. Where does it not fit yet?

- **No checkpoint/resume.** The feature the brief assumed does not exist in Python.
- **No generic agent adapter.** Only PydanticAI, LangGraph and OpenAI Agents. A harness
  built on raw provider SDKs — like RDAB — cannot be replayed without writing one.
- **Cost model mismatch.** Kitaru's replay saves tool execution and side effects. A
  benchmark's expense is model tokens, which replay re-spends.
- **Three different reference formats** for the same `--agent`-style flag across commands,
  which cost four debugging detours (FRICTION.md #8, #13, #14).

## 8. Useful feedback for ZenML/Kitaru

See `docs/kitaru_feedback_for_zenml.md`. The short version: document the custom-agent
protocol (it is ~10 env vars and a result shape), and state on the replay page that replay
re-spends model tokens, because "replay" reads as "cached" to anyone coming from a
benchmarking background.

## Honest limits of this experiment

- Two tasks, one model, one run each. Enough to prove the mechanics, not to characterise
  model behaviour.
- Replay reproduces *one past run*. It cannot tell you what the model would say today —
  for that you record again and compare.
- The recorded provider replays tool output too, so it does not re-validate that the
  generated code still runs against the current dataset generator.
- Four tests fail in the existing suite on `main` as well as on this branch (task counts
  drifted from 39 to 43, and the pricing table is 97 days stale). They are unrelated to
  this work; verified by running them in a clean `main` worktree.
