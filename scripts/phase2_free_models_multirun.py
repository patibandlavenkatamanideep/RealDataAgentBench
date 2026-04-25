"""
Phase 2 — Full multi-run CI for all 3 free models × 39 tasks × 5 runs.

Run this AFTER phase1_validate_new_tasks.py has completed and you've confirmed
the 16 new tasks look sane (reasonable scores, no broken ground truth).

Strategy
--------
- Target: 5 runs per (task, model) pair — gives a 95% CI with ~4 df
- Already done: 1 run each on 23 tasks (from the original leaderboard)
  and 1 run each on 16 new tasks (from Phase 1)
- Remaining work per model: 4 more runs × 39 tasks = 156 more runs per model
- Total new runs: 3 models × 156 = 468 runs
- Temperature: 1.0 (default) — we want natural sampling variance to appear
  in the CI, not artificially collapsed to 0

Sleep policy
------------
Groq free tier: ~30 requests/min documented; 30s sleep is safe (2 req/min).
Gemini free tier: 15 req/min; 20s sleep is safe.
xAI Grok free tier: 10 req/min documented; 20s sleep is safe.

Wall-clock estimate
-------------------
Groq  (Llama):  156 runs × (avg 60s task + 30s sleep) ≈ 3.9h
Gemini:         156 runs × (avg 45s task + 20s sleep) ≈ 3.1h
Grok-mini:      156 runs × (avg 50s task + 20s sleep) ≈ 3.5h
Total wall clock if run sequentially: ~10.5h — run overnight.

Usage
-----
    python3.14 scripts/phase2_free_models_multirun.py

Progress is printed to stdout. Interrupt-safe: re-running skips tasks that
already have 5 runs in the outputs/ directory.
"""

import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
PYTHON = sys.executable
RESULTS = ROOT / "docs" / "results.json"
OUTPUTS = ROOT / "outputs"

TARGET_RUNS = 5

ALL_TASKS = [
    "eda_001", "eda_002", "eda_003", "eda_004", "eda_005", "eda_006", "eda_007",
    "feat_001", "feat_002", "feat_003", "feat_004", "feat_005",
    "feat_006", "feat_009", "feat_010",
    "mod_001",  "mod_002",  "mod_003",  "mod_004",  "mod_005",
    "mod_006",  "mod_009",  "mod_010",
    "model_001","model_002","model_003","model_004","model_005",
    "model_006","model_009","model_010",
    "stat_001", "stat_002", "stat_003", "stat_004", "stat_005",
    "stat_006", "stat_009", "stat_010",
]

# (model_name, sleep_between_runs_seconds)
FREE_MODELS = [
    ("gemini-2.5-flash",        20),
    ("llama-3.3-70b-versatile", 30),
    ("grok-3-mini",             20),
]


def count_runs_from_outputs(model: str) -> dict[str, int]:
    """Count existing output files per task_id for a given model."""
    counts: dict[str, int] = defaultdict(int)
    for f in OUTPUTS.glob("*.json"):
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        if data.get("dry_run"):
            continue
        if data.get("model") != model:
            continue
        task = data.get("task_id")
        if task and not data.get("trace", {}).get("error"):
            counts[task] += 1
    return counts


def run_task(model: str, task_id: str) -> tuple[bool, str]:
    cmd = [PYTHON, "-m", "realdataagentbench.cli", "run", task_id,
           "--model", model]
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    elapsed = round(time.time() - t0)
    if result.returncode == 0:
        return True, f"OK ({elapsed}s)"
    err = (result.stderr or result.stdout)[-200:].strip().replace("\n", " ")
    return False, f"FAILED — {err[:120]}"


def rebuild_leaderboard() -> bool:
    r = subprocess.run(
        [PYTHON, str(ROOT / "scripts" / "build_leaderboard.py")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return r.returncode == 0


def main():
    print("=" * 70)
    print(f"PHASE 2 — Free models × 39 tasks × {TARGET_RUNS} runs (multi-run CI)")
    print(f"Models: {', '.join(m for m,_ in FREE_MODELS)}")
    print(f"Total target runs per model: {len(ALL_TASKS) * TARGET_RUNS}")
    print("=" * 70)

    grand_total_ran = 0
    grand_errors: list[tuple[str, str, str]] = []

    for model, sleep_sec in FREE_MODELS:
        existing = count_runs_from_outputs(model)
        needed = {t: TARGET_RUNS - existing.get(t, 0) for t in ALL_TASKS}
        to_run = [(t, n) for t, n in needed.items() if n > 0]

        if not to_run:
            print(f"\n[SKIP] {model} — already at {TARGET_RUNS} runs on all tasks")
            continue

        total_needed = sum(n for _, n in to_run)
        print(f"\n{'─'*60}")
        print(f"  {model}")
        print(f"  Existing runs: {dict(sorted(existing.items()))}")
        print(f"  Need {total_needed} more runs across {len(to_run)} tasks")
        print(f"  Sleep between runs: {sleep_sec}s  |  Est. time: ~{total_needed*(60+sleep_sec)/3600:.1f}h")
        print(f"{'─'*60}")

        model_ran = 0
        run_counter = 0
        for task, num_runs in sorted(to_run):
            for run_idx in range(num_runs):
                run_counter += 1
                print(
                    f"  [{run_counter:03d}/{total_needed}] {task} run {run_idx+1}/{num_runs} ... ",
                    end="", flush=True,
                )
                ok, status = run_task(model, task)
                print(status)
                if ok:
                    model_ran += 1
                    grand_total_ran += 1
                else:
                    grand_errors.append((model, task, status))
                time.sleep(sleep_sec)

        print(f"  {model}: {model_ran} runs completed")

        # Rebuild leaderboard after each model so progress is visible
        print("  Rebuilding leaderboard...", end="", flush=True)
        ok = rebuild_leaderboard()
        print(" OK" if ok else " FAILED")

        time.sleep(10)

    print(f"\n{'='*70}")
    print(f"PHASE 2 COMPLETE — {grand_total_ran} runs, {len(grand_errors)} errors")
    if grand_errors:
        print("\nFailed runs:")
        for m, t, e in grand_errors:
            print(f"  {m} / {t}: {e}")
    else:
        print("All runs succeeded. Leaderboard now has CI bounds for all 3 free models.")


if __name__ == "__main__":
    main()
