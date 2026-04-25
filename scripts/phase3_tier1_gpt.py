"""
Phase 3 — Tier 1 cheap GPT models × 39 tasks × 3 runs.

Models: gpt-4.1-nano, gpt-4.1-mini, gpt-4o-mini
Total new runs needed: 3 models × (39 tasks × 3 runs − existing 23×1) = ~282 runs
Estimated cost: ~$4.94 total

Run after Phase 2 confirms the 16 new tasks are sane.
Usage:  python3.14 scripts/phase3_tier1_gpt.py

OpenAI rate limits are generous at this volume — 5s sleep between runs is safe.
"""

import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
PYTHON = sys.executable
OUTPUTS = ROOT / "outputs"

TARGET_RUNS = 3

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

# sleep_sec: 5s is fine for OpenAI paid tier at this volume
TIER1_MODELS = [
    ("gpt-4.1-nano",  5),
    ("gpt-4.1-mini",  5),
    ("gpt-4o-mini",   5),
]


def count_runs_from_outputs(model: str) -> dict[str, int]:
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
    cmd = [PYTHON, "-m", "realdataagentbench.cli", "run", task_id, "--model", model]
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
    print(f"PHASE 3 — Tier 1 GPT × 39 tasks × {TARGET_RUNS} runs")
    print(f"Models: {', '.join(m for m,_ in TIER1_MODELS)}")
    print("Estimated cost: ~$4.94 total")
    print("=" * 70)

    grand_ran = 0
    grand_errors: list[tuple[str, str, str]] = []

    for model, sleep_sec in TIER1_MODELS:
        existing = count_runs_from_outputs(model)
        needed = {t: TARGET_RUNS - existing.get(t, 0) for t in ALL_TASKS}
        to_run = [(t, n) for t, n in sorted(needed.items()) if n > 0]

        total_needed = sum(n for _, n in to_run)
        if not to_run:
            print(f"\n[SKIP] {model} — already at {TARGET_RUNS} runs on all tasks")
            continue

        print(f"\n{'─'*60}")
        print(f"  {model}  ({total_needed} runs needed)")
        print(f"{'─'*60}")

        run_counter = 0
        for task, num_runs in to_run:
            for run_idx in range(num_runs):
                run_counter += 1
                print(
                    f"  [{run_counter:03d}/{total_needed}] {task} run {run_idx+1}/{num_runs} ... ",
                    end="", flush=True,
                )
                ok, status = run_task(model, task)
                print(status)
                if ok:
                    grand_ran += 1
                else:
                    grand_errors.append((model, task, status))
                time.sleep(sleep_sec)

        print("  Rebuilding leaderboard...", end="", flush=True)
        ok = rebuild_leaderboard()
        print(" OK" if ok else " FAILED")
        time.sleep(5)

    print(f"\n{'='*70}")
    print(f"PHASE 3 COMPLETE — {grand_ran} runs, {len(grand_errors)} errors")
    if grand_errors:
        for m, t, e in grand_errors:
            print(f"  {m} / {t}: {e}")


if __name__ == "__main__":
    main()
