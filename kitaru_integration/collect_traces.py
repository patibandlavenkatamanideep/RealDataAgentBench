"""Build a Kitaru import payload from RDAB run outputs.

Reads every run JSON under an outputs directory, scores it with RDAB's own
CompositeScorer (unchanged — same scorer the leaderboard uses), attaches the
scorecard under "scores", and writes one JSON object per line.

    python kitaru_integration/collect_traces.py outputs/kitaru rdab_sessions.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from realdataagentbench.core.registry import TaskRegistry
from realdataagentbench.scoring.composite import CompositeScorer


def main(outputs_dir: str, destination: str, variant: str = "baseline") -> None:
    repo_root = Path(__file__).resolve().parent.parent
    registry = TaskRegistry(repo_root / "tasks")
    scorer = CompositeScorer()

    runs = sorted(p for p in Path(outputs_dir).rglob("*.json") if p.name != "manifest.json")
    written = 0
    with Path(destination).open("w") as out:
        for path in runs:
            run = json.loads(path.read_text())
            if "trace" not in run:          # dry-run artefacts have no trace
                continue
            card = scorer.score(registry.get(run["task_id"]), run)
            run["scores"] = {
                "correctness": card.correctness,
                "code_quality": card.code_quality,
                "efficiency": card.efficiency,
                "stat_validity": card.stat_validity,
                "dab_score": card.dab_score,
            }
            run["source_file"] = str(path.resolve().relative_to(repo_root))
            run["variant"] = variant
            out.write(json.dumps(run) + "\n")
            written += 1
            print(f"  {run['task_id']:10} {run['model']:26} "
                  f"corr {card.correctness:.2f}  valid {card.stat_validity:.2f}  "
                  f"dab {card.dab_score:.3f}")
    print(f"wrote {written} sessions -> {destination}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "outputs/kitaru",
         sys.argv[2] if len(sys.argv) > 2 else "rdab_sessions.jsonl",
         sys.argv[3] if len(sys.argv) > 3 else "baseline")
