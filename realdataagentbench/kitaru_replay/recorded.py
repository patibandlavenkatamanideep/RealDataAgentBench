"""Serve a benchmark run from a recorded trace instead of a live provider.

This is the offline half of the lab. A recorded run already contains every assistant
turn and tool result, so replaying it exercises the same scoring path at zero cost and
with no API key — which is what makes the experiment safe to run in CI.

It deliberately replays *what the model said*, not what the tools computed: tool output
is taken from the recording too, so a replay is a faithful reproduction of one past run
rather than a fresh execution against today's data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..harness.tracer import Tracer


class RecordedRunNotFound(LookupError):
    """No recorded run matches the requested task and model."""


def find_recording(outputs_dir: Path | str, task_id: str, model: str) -> Path:
    """Newest successful recording for this (task, model), or raise."""
    candidates = []
    for path in Path(outputs_dir).rglob("*.json"):
        if path.name == "manifest.json":
            continue
        try:
            run = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        trace = run.get("trace") or {}
        if run.get("task_id") != task_id or run.get("model") != model:
            continue
        if trace.get("error") or not trace.get("final_answer"):
            continue          # a failed run is not a useful thing to replay
        candidates.append((path.stat().st_mtime, path))
    if not candidates:
        raise RecordedRunNotFound(
            f"no successful recording for task={task_id!r} model={model!r} under {outputs_dir}"
        )
    return max(candidates)[1]


class RecordedProvider:
    """Drop-in stand-in for a provider that replays a recorded trace.

    Matches the shape the harness expects (`run(...) -> final_answer`, recording steps
    into the tracer), so the scoring path downstream cannot tell the difference.
    """

    def __init__(self, recording_path: Path | str):
        self.recording_path = Path(recording_path)
        self.run_data: dict[str, Any] = json.loads(self.recording_path.read_text())
        self.trace: dict[str, Any] = self.run_data["trace"]

    @property
    def model(self) -> str:
        return self.run_data.get("model", "recorded")

    def run(self, tracer: Tracer | None = None, **_: Any) -> str:
        """Replay every recorded step into `tracer` and return the recorded answer."""
        for step in self.trace.get("steps", []):
            if tracer is not None:
                tracer.record(
                    role=step.get("role", "assistant"),
                    content=step.get("content") or "",
                    tool_name=step.get("tool_name"),
                    tool_input=step.get("tool_input"),
                    tool_output=step.get("tool_output"),
                    input_tokens=step.get("input_tokens", 0),
                    output_tokens=step.get("output_tokens", 0),
                )
        return self.trace.get("final_answer", "")

    def usage(self) -> dict[str, int]:
        return {
            "input_tokens": self.trace.get("total_input_tokens", 0),
            "output_tokens": self.trace.get("total_output_tokens", 0),
            "num_steps": self.trace.get("num_steps", 0),
        }
