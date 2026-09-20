"""The RDAB execution path, split into serializable steps.

Kitaru has no `@checkpoint` decorator (see docs/kitaru_replay_findings.md), so a
"checkpoint" here is an explicit function with a JSON-serializable return value. That
buys the two things checkpoints are for:

  * each step can be timed, cached and replayed independently;
  * each step maps onto one Kitaru session node when the run is imported.

Step boundaries follow the brief: load case, build input, run model, score, write row.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.registry import TaskRegistry
from ..datasets import get_generator
from ..harness.tracer import Tracer
from ..scoring.composite import CompositeScorer

STEP_NAMES = ("load_benchmark_case", "build_model_input", "run_model", "score_output",
              "write_result_row")


@dataclass
class StepRecord:
    """One executed step: what it produced, how long it took, and whether it was replayed."""
    name: str
    seconds: float
    replayed: bool
    output: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"step": self.name, "seconds": round(self.seconds, 4),
                "replayed": self.replayed, "output": self.output}


class _Timer:
    def __init__(self) -> None:
        self.started = time.perf_counter()

    @property
    def elapsed(self) -> float:
        return time.perf_counter() - self.started


def load_benchmark_case(task_id: str, tasks_dir: Path | str) -> tuple[Any, Any, StepRecord]:
    """Checkpoint 1 — resolve the task and materialise its dataset (deterministic)."""
    timer = _Timer()
    task = TaskRegistry(Path(tasks_dir)).get(task_id)
    generator = get_generator(task.dataset.generator)
    frame = generator(n_rows=task.dataset.n_rows, seed=task.dataset.seed)
    record = StepRecord(
        "load_benchmark_case", timer.elapsed, replayed=False,
        output={"task_id": task.task_id, "category": task.category,
                "difficulty": task.difficulty, "dataset_shape": list(frame.shape),
                "dataset_seed": task.dataset.seed},
    )
    return task, frame, record


def build_model_input(task: Any) -> tuple[str, StepRecord]:
    """Checkpoint 2 — the prompt actually sent, hashed so a change is visible."""
    timer = _Timer()
    prompt = task.description
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    return prompt, StepRecord(
        "build_model_input", timer.elapsed, replayed=False,
        output={"prompt_chars": len(prompt), "prompt_sha256": f"sha256:{digest[:16]}"},
    )


def run_model(task: Any, frame: Any, provider: Any, *, replayed: bool) -> tuple[dict, StepRecord]:
    """Checkpoint 3 — the expensive step. Either a live agent loop or a recorded replay."""
    timer = _Timer()
    tracer = Tracer(task_id=task.task_id, model=getattr(provider, "model", "unknown"))
    if replayed:
        answer = provider.run(tracer=tracer)
        error = None
    else:
        from ..harness.agent import Agent
        agent = Agent(model=provider)
        trace = agent.run(
            task_description=task.description, dataframe=frame, task_id=task.task_id,
            max_steps=task.evaluation.max_steps,
            timeout_seconds=task.evaluation.timeout_seconds,
            allowed_tools=task.evaluation.allowed_tools,
        )
        return ({"trace": trace.to_dict()},
                StepRecord("run_model", timer.elapsed, replayed=False,
                           output={"num_steps": trace.to_dict().get("num_steps", 0),
                                   "tokens": trace.total_input_tokens + trace.total_output_tokens}))
    trace = tracer.finalize(final_answer=answer, error=error)
    payload = {"trace": trace.to_dict()}
    return payload, StepRecord(
        "run_model", timer.elapsed, replayed=True,
        output={"num_steps": payload["trace"].get("num_steps", 0),
                "tokens": payload["trace"].get("total_input_tokens", 0)
                + payload["trace"].get("total_output_tokens", 0)},
    )


def score_output(task: Any, model_result: dict) -> tuple[dict, StepRecord]:
    """Checkpoint 4 — RDAB's own CompositeScorer, unchanged."""
    timer = _Timer()
    card = CompositeScorer().score(task, model_result)
    scores = card.to_dict()
    return scores, StepRecord(
        "score_output", timer.elapsed, replayed=False,
        output={k: scores[k] for k in
                ("correctness", "code_quality", "efficiency", "stat_validity", "dab_score")},
    )


def write_result_row(destination: Path | str, row: dict) -> StepRecord:
    """Checkpoint 5 — persist the artifact."""
    timer = _Timer()
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(row) + "\n")
    return StepRecord("write_result_row", timer.elapsed, replayed=False,
                      output={"path": str(path), "bytes": len(json.dumps(row))})


def run_case(task_id: str, provider: Any, *, tasks_dir: Path | str, out_file: Path | str,
             replayed: bool) -> dict[str, Any]:
    """The flow: the five steps above, in order, with per-step timings."""
    steps: list[StepRecord] = []
    task, frame, rec = load_benchmark_case(task_id, tasks_dir); steps.append(rec)
    _prompt, rec = build_model_input(task); steps.append(rec)
    model_result, rec = run_model(task, frame, provider, replayed=replayed); steps.append(rec)
    scores, rec = score_output(task, model_result); steps.append(rec)

    trace = model_result["trace"]
    row = {
        "task_id": task_id,
        "model": getattr(provider, "model", str(provider)),
        "mode": "replayed" if replayed else "live",
        "scores": scores,
        "tokens": trace.get("total_input_tokens", 0) + trace.get("total_output_tokens", 0),
        "input_tokens": trace.get("total_input_tokens", 0),
        "output_tokens": trace.get("total_output_tokens", 0),
        "num_steps": trace.get("num_steps", 0),
        "final_answer_chars": len(trace.get("final_answer") or ""),
        "steps": [s.to_dict() for s in steps],
    }
    steps.append(write_result_row(out_file, row))
    row["steps"] = [s.to_dict() for s in steps]
    row["wall_seconds"] = round(sum(s.seconds for s in steps), 4)
    return row
