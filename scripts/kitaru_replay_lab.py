"""Kitaru Replay Lab — replay a tiny RDAB subset and report what replay actually saves.

Offline by default: model output is served from recorded runs under --recordings, so the
lab needs no API key and costs nothing. Live mode exists for producing new recordings and
requires RDAB_LAB_ALLOW_LIVE=1 because it spends money.

    python scripts/kitaru_replay_lab.py \
      --tasks feat_001,feat_003 --model gemini-2.5-flash --runs 1 \
      --out artifacts/kitaru_replay/

Findings template and results land in the --out directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from realdataagentbench.harness.pricing import compute_cost  # noqa: E402
from realdataagentbench.kitaru_replay import (  # noqa: E402
    RecordedProvider,
    RecordedRunNotFound,
    run_case,
)
from realdataagentbench.kitaru_replay.recorded import find_recording  # noqa: E402

LIVE_ENV = "RDAB_LAB_ALLOW_LIVE"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tasks", required=True, help="Comma-separated task ids, e.g. feat_001,feat_003")
    p.add_argument("--model", required=True, help="Model name as RDAB knows it")
    p.add_argument("--runs", type=int, default=1, help="Repeats per task (default 1)")
    p.add_argument("--out", default="artifacts/kitaru_replay", help="Artifact directory")
    p.add_argument("--recordings", default="outputs/kitaru",
                   help="Directory of recorded runs used by replay mode")
    p.add_argument("--mode", choices=("replay", "live"), default="replay",
                   help="replay (default, free) or live (spends money)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_file = out_dir / "results.jsonl"

    if args.mode == "live" and os.environ.get(LIVE_ENV) != "1":
        print(f"Refusing to run live: set {LIVE_ENV}=1 to allow paid API calls.\n"
              f"Live mode calls {args.model} once per task per run and costs real money.",
              file=sys.stderr)
        return 2

    rows = []
    for task_id in tasks:
        for _ in range(args.runs):
            if args.mode == "replay":
                try:
                    recording = find_recording(args.recordings, task_id, args.model)
                except RecordedRunNotFound as exc:
                    print(f"  {task_id}: {exc}", file=sys.stderr)
                    print(f"  produce one first: RDAB_LAB_ALLOW_LIVE=1 {sys.argv[0]} "
                          f"--tasks {task_id} --model {args.model} --mode live", file=sys.stderr)
                    return 1
                provider = RecordedProvider(recording)
                row = run_case(task_id, provider, tasks_dir=REPO_ROOT / "tasks",
                               out_file=results_file, replayed=True)
                row["recording"] = str(recording)
            else:
                row = run_case(task_id, args.model, tasks_dir=REPO_ROOT / "tasks",
                               out_file=results_file, replayed=False)
            row["cost_usd"] = 0.0 if args.mode == "replay" else (
                compute_cost(args.model, row.get("input_tokens", 0),
                             row.get("output_tokens", 0)) or 0.0)
            rows.append(row)
            print(f"  {task_id:10} {args.mode:7} dab={row['scores']['dab_score']:.3f} "
                  f"validity={row['scores']['stat_validity']:.2f} "
                  f"tokens={row['tokens']:6} {row['wall_seconds']:.2f}s")

    summary = summarise(rows, args)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\n{len(rows)} case(s) -> {results_file}")
    print(f"summary -> {out_dir / 'summary.json'}")
    if args.mode == "replay":
        print(f"model tokens served from recordings: {summary['tokens_served_from_recording']:,} "
              f"(${summary['cost_avoided_usd']:.4f} not spent)")
    return 0


def summarise(rows: list[dict], args: argparse.Namespace) -> dict:
    """Aggregate, and price what replay avoided at the model's real rate."""
    avoided = 0.0
    for row in rows:
        if row["mode"] == "replayed":
            # price the recorded traffic as if it had been paid for again, splitting
            # input and output because they bill at different rates
            avoided += compute_cost(row["model"], row.get("input_tokens", 0),
                                    row.get("output_tokens", 0)) or 0.0
    per_step: dict[str, float] = {}
    for row in rows:
        for step in row["steps"]:
            per_step[step["step"]] = per_step.get(step["step"], 0.0) + step["seconds"]
    return {
        "mode": args.mode,
        "model": args.model,
        "tasks": [r["task_id"] for r in rows],
        "cases": len(rows),
        "mean_dab_score": round(sum(r["scores"]["dab_score"] for r in rows) / len(rows), 4),
        "mean_stat_validity": round(sum(r["scores"]["stat_validity"] for r in rows) / len(rows), 4),
        "tokens_served_from_recording": sum(r["tokens"] for r in rows if r["mode"] == "replayed"),
        "cost_avoided_usd": round(avoided, 6),
        "seconds_per_step": {k: round(v, 4) for k, v in per_step.items()},
        "wall_seconds": round(sum(r["wall_seconds"] for r in rows), 3),
    }


if __name__ == "__main__":
    raise SystemExit(main())
