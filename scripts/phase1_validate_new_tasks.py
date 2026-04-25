"""
Phase 1 — Validate 16 new tasks on 3 free models (1 run each = 48 runs).

Models: gemini-2.5-flash, llama-3.3-70b-versatile, grok-3-mini
New tasks: eda_004–007, feat_006/009/010, mod_006/009/010,
           model_006/009/010, stat_006/009/010

Sleep policy:
  - 30s between runs on Groq (Llama) — free-tier rate limit
  - 20s between runs on Gemini free tier
  - 20s between runs on xAI Grok free tier
  - 10s between models

After all runs: rebuild leaderboard + print a quick sanity report.
Run this from the repo root:  python3.14 scripts/phase1_validate_new_tasks.py
"""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
PYTHON = sys.executable          # whatever python3.14 invoked this script
RESULTS = ROOT / "docs" / "results.json"
OUTPUTS = ROOT / "outputs"

NEW_TASKS = [
    "eda_004", "eda_005", "eda_006", "eda_007",
    "feat_006", "feat_009", "feat_010",
    "mod_006",  "mod_009",  "mod_010",
    "model_006","model_009","model_010",
    "stat_006", "stat_009", "stat_010",
]

# (model_name, sleep_between_runs_seconds)
FREE_MODELS = [
    ("gemini-2.5-flash",        20),
    ("llama-3.3-70b-versatile", 30),
    ("grok-3-mini",             20),
]


def already_done() -> set[tuple[str, str]]:
    """Return set of (model, task_id) pairs already in the leaderboard."""
    if not RESULTS.exists():
        return set()
    data = json.loads(RESULTS.read_text())
    return {(r["model"], r["task_id"]) for r in data["runs"]}


def run_task(model: str, task_id: str) -> tuple[bool, str]:
    """Run one task. Returns (success, short_status_string)."""
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


def sanity_report():
    """Print token counts + scores for new tasks to help spot broken ground truth."""
    if not RESULTS.exists():
        return
    data = json.loads(RESULTS.read_text())
    rows = [r for r in data["runs"] if r["task_id"] in NEW_TASKS]
    if not rows:
        print("  (no rows for new tasks yet)")
        return

    print(f"\n{'Task':<14} {'Model':<30} {'DAB':>5} {'Corr':>5} {'Stat':>5} {'Tokens':>8} {'Cost':>8}")
    print("-" * 82)
    for r in sorted(rows, key=lambda x: (x["task_id"], x["model"])):
        print(
            f"{r['task_id']:<14} {r['model']:<30} "
            f"{r['dab_score']:>5.3f} {r['correctness']:>5.3f} "
            f"{r['stat_validity']:>5.3f} {r['total_tokens']:>8,} "
            f"${r['avg_cost_usd']:>7.5f}"
        )


def main():
    done = already_done()
    total_ran = 0
    errors: list[tuple[str, str, str]] = []

    print("=" * 70)
    print("PHASE 1 — Validate 16 new tasks on 3 free models")
    print(f"New tasks: {len(NEW_TASKS)}   Models: {len(FREE_MODELS)}   Target runs: {len(NEW_TASKS)*len(FREE_MODELS)}")
    print("=" * 70)

    for model, sleep_sec in FREE_MODELS:
        to_run = [t for t in NEW_TASKS if (model, t) not in done]
        if not to_run:
            print(f"\n[SKIP] {model} — all 16 new tasks already done")
            continue

        print(f"\n{'─'*60}")
        print(f"  {model}  ({len(to_run)} tasks, {sleep_sec}s sleep between runs)")
        print(f"{'─'*60}")

        for i, task in enumerate(to_run):
            print(f"  [{i+1:02d}/{len(to_run)}] {task} ... ", end="", flush=True)
            ok, status = run_task(model, task)
            print(status)
            if ok:
                total_ran += 1
            else:
                errors.append((model, task, status))
            # Sleep between runs to respect free-tier rate limits
            if i < len(to_run) - 1:
                time.sleep(sleep_sec)

        # Brief pause between models
        time.sleep(10)

    print(f"\n{'='*70}")
    print(f"DONE — {total_ran} runs completed, {len(errors)} errors")
    if errors:
        print("\nFailed runs (investigate before Phase 2):")
        for m, t, e in errors:
            print(f"  {m} / {t}: {e}")

    # Rebuild leaderboard
    if total_ran > 0:
        print("\nRebuilding leaderboard...", end="", flush=True)
        ok = rebuild_leaderboard()
        print(" OK" if ok else " FAILED")

    # Sanity report
    print("\n── Sanity check: new task scores ──")
    sanity_report()

    # Summary flag
    if errors:
        print(f"\n⚠️  {len(errors)} runs failed. Inspect tasks before running Phase 2.")
    else:
        print(f"\n✓ All {total_ran} validation runs succeeded. Ready for Phase 2.")


if __name__ == "__main__":
    main()
