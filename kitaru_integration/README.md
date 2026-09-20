# RDAB × Kitaru integration

Runs RealDataAgentBench tasks, imports the traces into [Kitaru](https://github.com/zenml-io/kitaru)
as sessions, scores statistical validity with a Kitaru evaluator that wraps RDAB's own
scorer, and compares a baseline against a candidate prompt.

Everything below was executed on 2026-09-19 against Kitaru 0.26.0 running locally.
Total API spend for the full reproduction: **$1.80**.

## What this does and does not do

| | |
|---|---|
| ✅ | RDAB traces become Kitaru sessions, with per-step `llm_call` / `tool_call` nodes, token usage and cost |
| ✅ | `stat_validity` runs as a registered Kitaru evaluator, reporting which of its four checks failed |
| ✅ | Baseline and candidate runs sit side by side in one evidence store and are compared by the same evaluator |
| ❌ | `kitaru replay create` cannot re-run RDAB. Replay executes the agent's command verbatim; a custom agent must implement Kitaru's (undocumented) adapter protocol first. See FRICTION.md #7 |

Because of that last row, the candidate runs are produced by RDAB itself (`dab run` with a
prompt flag), not by a Kitaru replay. Kitaru does the measuring and holds the evidence;
it does not drive the re-run.

## Reproduce

```bash
# 0. prerequisites: Python 3.11+, Docker with Compose v2 (Podman is rejected — FRICTION.md #5)
uv venv ~/.venvs/rdab --python 3.13
uv pip install --python ~/.venvs/rdab/bin/python -e . "kitaru[cli,mcp,worker]"
export PATH="$HOME/.venvs/rdab/bin:$PATH"

cp .env.example .env     # add ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY

# 1. local Kitaru server (~30s once images are pulled)
kitaru login --local --no-browser
kitaru worker start &            # a worker is required even to import

# 2. baseline: 3 tasks x 3 models
for m in gemini-2.5-flash gpt-4o-mini claude-sonnet-4-6; do
  for t in feat_003 feat_001 mod_004; do
    dab run "$t" --model "$m" --output-dir "outputs/kitaru/$m" --budget 0.50
  done
done

# 3. import them as Kitaru sessions
python kitaru_integration/collect_traces.py outputs/kitaru kitaru_integration/rdab_sessions.jsonl baseline
kitaru importer register rdab --script kitaru_integration/rdab_importer.py --entrypoint parse --provider rdab
kitaru agent register rdab-agent --command "dab run {task_id} --model {model}" --working-dir "$PWD"
kitaru session import kitaru_integration/rdab_sessions.jsonl --importer rdab@latest --agent rdab-agent@latest --wait

# 4. register the evaluator and score every session
kitaru evaluator register stat-validity --script kitaru_integration/stat_validity_evaluator.py --entrypoint evaluate
kitaru session evaluate --all --evaluator stat-validity@latest --wait --timeout 300

# 5. candidate: same tasks, statistical-validity prompt addendum enabled
RDAB_STAT_VALIDITY_PROMPT=1 dab run feat_001 --model gemini-2.5-flash \
  --output-dir outputs/kitaru-candidate/gemini-2.5-flash --budget 2.00
# ...repeat for the other target cases, then:
python kitaru_integration/collect_traces.py outputs/kitaru-candidate kitaru_integration/rdab_candidate.jsonl candidate
kitaru importer version register rdab --script kitaru_integration/rdab_importer.py --entrypoint parse
kitaru session import kitaru_integration/rdab_candidate.jsonl --importer rdab@latest --agent rdab-agent@latest --wait
kitaru session evaluate --all --evaluator stat-validity@latest --wait --timeout 300
```

The dashboard is at http://localhost:8000.

## Files

| file | role |
|---|---|
| `rdab_importer.py` | RDAB run JSON → `ImportedSession` / `ImportedNode`. One trace step becomes one node |
| `collect_traces.py` | Walks an outputs directory, scores each run with RDAB's `CompositeScorer`, writes the JSONL payload |
| `stat_validity_evaluator.py` | Kitaru evaluator wrapping RDAB's `StatValidityScorer`, reporting the four sub-checks |

## Changes to the benchmark itself

Two, both on this branch and both needed before anything could run:

1. **`providers.py` — Anthropic temperature.** `anthropic` 1.x removed `temperature` from
   `messages.create()`, so *every* Claude run failed instantly with a `TypeError`. The
   provider now asks the installed SDK whether the parameter exists instead of keeping a
   version table.
2. **`providers.py` — opt-in prompt addendum.** `RDAB_STAT_VALIDITY_PROMPT=1` appends a
   request for quantified uncertainty, named methods and stated limitations. **Off by
   default**, so the existing runner and every recorded leaderboard result are unchanged.

The addendum deliberately does not name the scorer's regex vocabulary. `stat_validity` is
lexical, so feeding it the words it greps for would raise the score without improving the
analysis.
