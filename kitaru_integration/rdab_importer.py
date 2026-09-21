"""Kitaru importer for RealDataAgentBench run files.

RDAB writes one JSON per run (see harness/runner.py::_save_result) containing the task
metadata and a Trace: ordered steps, each either an assistant turn (model call, with
token counts) or a tool result (run_code / get_dataframe_info / get_column_stats).

This maps one RDAB run to one Kitaru session, and one trace step to one node:

    assistant step -> node_type "llm_call"   (tokens attached)
    tool step      -> node_type "tool_call"  (tool_name, inputs, outputs)

Payload format: JSON Lines, one RDAB run object per line. `scripts/collect_traces.py`
builds it from an outputs/ directory and attaches RDAB's own scorecard under "scores",
which lands in session metadata so it can be queried before any evaluator runs.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from typing import Any

from kitaru.api_models.v1.session import TokenUsage
from kitaru.task.importer import ImportedNode, ImportFailure, ImportedSession, Parser

FRAMEWORK = "realdataagentbench"


def _aware(value: str | None) -> datetime | None:
    """RDAB stamps UTC ISO strings; Kitaru requires timezone-aware datetimes."""
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _nodes(trace: dict, model: str, started: datetime | None) -> list[ImportedNode]:
    nodes: list[ImportedNode] = []
    clock = started
    for i, step in enumerate(trace.get("steps", [])):
        elapsed = float(step.get("elapsed_seconds") or 0.0)
        node_started = clock
        node_ended = clock + timedelta(seconds=elapsed) if clock else None
        clock = node_ended

        if step.get("role") == "tool":
            nodes.append(ImportedNode(
                index=i,
                node_type="tool_call",
                name=step.get("tool_name") or "tool",
                tool_name=step.get("tool_name"),
                status="completed",
                inputs=step.get("tool_input") or {},
                outputs={"result": step.get("tool_output"), "text": step.get("content")},
                started_at=node_started,
                ended_at=node_ended,
                attributes={},
            ))
            continue

        tokens = TokenUsage(
            input_tokens=step.get("input_tokens") or 0,
            output_tokens=step.get("output_tokens") or 0,
        )
        nodes.append(ImportedNode(
            index=i,
            node_type="llm_call",
            name="assistant",
            status="completed",
            inputs={},
            outputs={"text": step.get("content") or ""},
            requested_model=model,
            model=model,
            tokens=tokens,
            started_at=node_started,
            ended_at=node_ended,
            attributes={},
        ))
    return nodes


def parse(payload: bytes, params: dict[str, Any]) -> Iterator[ImportedSession | ImportFailure]:
    """Yield one ImportedSession per RDAB run object. Lazily, one line at a time."""
    for lineno, raw in enumerate(payload.decode("utf-8").splitlines(), start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            run = json.loads(raw)
            trace = run["trace"]
            model = run.get("model") or trace.get("model") or "unknown"
            task_id = run.get("task_id") or trace.get("task_id") or "unknown"
            ended = _aware(run.get("run_at"))
            elapsed = float(trace.get("total_elapsed_seconds") or 0.0)
            started = ended - timedelta(seconds=elapsed) if ended else None
            error = trace.get("error")
            scores = run.get("scores") or {}

            yield ImportedSession(
                external_id=f"{task_id}::{model}::{run.get('run_at')}",
                name=f"{task_id} · {model}",
                status="failed" if error else "completed",
                framework=FRAMEWORK,
                inputs={"task_id": task_id, "title": run.get("title"),
                        "category": run.get("category"), "difficulty": run.get("difficulty"),
                        "dataset_shape": run.get("dataset_shape")},
                outputs={"final_answer": trace.get("final_answer", "")},
                error=error,
                started_at=started,
                ended_at=ended,
                input_text_selector="task_id",
                output_text_selector="final_answer",
                metadata={
                    "task_id": task_id, "model": model,
                    "variant": run.get("variant", "baseline"),
                    "category": run.get("category"), "difficulty": run.get("difficulty"),
                    "total_input_tokens": trace.get("total_input_tokens", 0),
                    "total_output_tokens": trace.get("total_output_tokens", 0),
                    "num_steps": trace.get("num_steps", 0),
                    # RDAB's own scorecard, attached by collect_traces.py
                    **{f"score_{k}": v for k, v in scores.items()
                       if isinstance(v, (int, float, str))},
                },
                nodes=_nodes(trace, model, started),
            )
        except Exception as exc:  # one bad line must not abort the import
            yield ImportFailure(line=lineno, error=f"{type(exc).__name__}: {exc}")


parser: Parser = parse
