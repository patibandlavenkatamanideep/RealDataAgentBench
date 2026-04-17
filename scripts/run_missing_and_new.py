"""
Run missing tasks for existing models + benchmark new models.
Skips tasks already completed. Prints cost summary at the end.

Coverage status (2026-04-17 after batch 1):
  gpt-4o-mini           20/23  — 3 remaining (~$0.05)
  gpt-4.1-nano          19/23  — 4 remaining (~$0.04)
  claude-opus-4-6       17/23  — 6 remaining (~$11.52) ← needs Anthropic credits
  claude-sonnet-4-6      9/23  — 14 remaining (~$6.66) ← needs Anthropic credits
  claude-haiku-4-5       8/23  — 15 remaining (~$0.94) ← needs Anthropic credits
"""
import subprocess, sys, json, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
VENV_PYTHON = str(ROOT / ".venv/bin/python")
RESULTS = ROOT / "docs/results.json"

# ── load already-completed runs ──────────────────────────────────────────────
with open(RESULTS) as f:
    data = json.load(f)

done = set()
for r in data["runs"]:
    done.add((r["model"], r["task_id"]))

ALL_TASKS = sorted(set(r["task_id"] for r in data["runs"]))

# ── what to run ───────────────────────────────────────────────────────────────
# OpenAI tasks (~$0.09 total) — run first, no credit issues.
# Anthropic tasks — commented out until credits are topped up.
PLAN = [
    # 3 tasks — OpenAI, ~$0.05 total
    ("gpt-4o-mini", [
        "mod_001",
        "model_001", "model_003",
    ]),
    # 4 tasks — OpenAI, ~$0.04 total
    ("gpt-4.1-nano", [
        "feat_003", "mod_004",
        "model_005", "stat_004",
    ]),
    # ── Anthropic models — uncomment after adding credits ────────────────────
    # 6 tasks — Anthropic Opus, ~$11.52 total
    # ("claude-opus-4-6", [
    #     "model_005",
    #     "stat_001", "stat_002", "stat_003", "stat_004", "stat_005",
    # ]),
    # 14 tasks — Anthropic Sonnet, ~$6.66 total
    # ("claude-sonnet-4-6", [
    #     "mod_001", "mod_003", "mod_004", "mod_005",
    #     "model_001", "model_002", "model_003", "model_004", "model_005",
    #     "stat_001", "stat_002", "stat_003", "stat_004", "stat_005",
    # ]),
    # 15 tasks — Anthropic Haiku, ~$0.94 total
    # ("claude-haiku-4-5-20251001", [
    #     "mod_001", "mod_002", "mod_003", "mod_004", "mod_005",
    #     "model_001", "model_002", "model_003", "model_004", "model_005",
    #     "stat_001", "stat_002", "stat_003", "stat_004", "stat_005",
    # ]),
]

# ── runner ────────────────────────────────────────────────────────────────────
total_ran = 0
errors = []

for model, tasks in PLAN:
    to_run = [t for t in tasks if (model, t) not in done]
    if not to_run:
        print(f"[SKIP] {model} — all tasks already done")
        continue
    print(f"\n{'='*60}")
    print(f"MODEL: {model}  ({len(to_run)} tasks to run)")
    print(f"{'='*60}")
    for task in to_run:
        print(f"  → {task} ... ", end="", flush=True)
        t0 = time.time()
        result = subprocess.run(
            [VENV_PYTHON, "-m", "realdataagentbench.cli", "run", task, "--model", model],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        elapsed = time.time() - t0
        if result.returncode == 0:
            # extract score from output
            score_line = [l for l in result.stdout.splitlines() if "RDAB" in l or "Score" in l]
            score_str = score_line[-1].strip() if score_line else ""
            print(f"OK ({elapsed:.0f}s)  {score_str}")
            total_ran += 1
        else:
            err = result.stderr[-300:] if result.stderr else result.stdout[-300:]
            print(f"FAILED — {err.strip()[:120]}")
            errors.append((model, task, err.strip()[:200]))

print(f"\n{'='*60}")
print(f"DONE — {total_ran} tasks run successfully, {len(errors)} errors")
if errors:
    print("\nFailed runs:")
    for model, task, err in errors:
        print(f"  {model} / {task}: {err[:100]}")

# ── rebuild leaderboard ───────────────────────────────────────────────────────
if total_ran > 0:
    print("\nRebuilding leaderboard...")
    r = subprocess.run(
        [VENV_PYTHON, str(ROOT / "scripts/build_leaderboard.py")],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    if r.returncode == 0:
        print("Leaderboard rebuilt OK")
    else:
        print(f"Leaderboard rebuild failed: {r.stderr[-200:]}")
