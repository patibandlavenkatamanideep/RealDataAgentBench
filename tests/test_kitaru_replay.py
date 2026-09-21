"""Tests for the Kitaru Replay Lab. No API key, no network, no cost."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from realdataagentbench.harness.tracer import Tracer
from realdataagentbench.kitaru_replay import STEP_NAMES, RecordedProvider, run_case
from realdataagentbench.kitaru_replay.recorded import RecordedRunNotFound, find_recording

REPO_ROOT = Path(__file__).resolve().parent.parent
RECORDINGS = REPO_ROOT / "outputs" / "kitaru"
pytestmark = pytest.mark.skipif(
    not RECORDINGS.exists(), reason="no recorded runs checked out; see kitaru_replay docs"
)


def _write_recording(tmp_path: Path, *, task_id="t1", model="m1", error=None, answer="ok") -> Path:
    run = {
        "task_id": task_id, "model": model, "run_at": "2026-09-20T00:00:00+00:00",
        "trace": {
            "task_id": task_id, "model": model, "final_answer": answer,
            "total_input_tokens": 100, "total_output_tokens": 20,
            "total_elapsed_seconds": 1.0, "num_steps": 2, "error": error,
            "steps": [
                {"step": 1, "role": "assistant", "content": "thinking",
                 "input_tokens": 100, "output_tokens": 20},
                {"step": 2, "role": "tool", "content": "{}", "tool_name": "run_code",
                 "tool_input": {"code": "df.shape"}, "tool_output": "(5, 2)"},
            ],
        },
    }
    path = tmp_path / f"{task_id}_{model}.json"
    path.write_text(json.dumps(run))
    return path


def test_recorded_provider_replays_every_step(tmp_path):
    provider = RecordedProvider(_write_recording(tmp_path))
    tracer = Tracer(task_id="t1", model="m1")
    answer = provider.run(tracer=tracer)

    assert answer == "ok"
    assert len(tracer.trace.steps) == 2
    assert tracer.trace.total_input_tokens == 100
    assert tracer.trace.total_output_tokens == 20
    assert [s.tool_name for s in tracer.trace.steps] == [None, "run_code"]
    assert provider.usage() == {"input_tokens": 100, "output_tokens": 20, "num_steps": 2}


def test_find_recording_prefers_successful_runs(tmp_path):
    _write_recording(tmp_path, error="Budget exceeded", answer="")
    good = _write_recording(tmp_path, model="m2")
    assert find_recording(tmp_path, "t1", "m2") == good
    with pytest.raises(RecordedRunNotFound, match="no successful recording"):
        find_recording(tmp_path, "t1", "m1")     # only the failed one exists


def test_missing_recording_names_the_task_and_model(tmp_path):
    with pytest.raises(RecordedRunNotFound) as exc:
        find_recording(tmp_path, "nope", "gpt-4o-mini")
    assert "nope" in str(exc.value) and "gpt-4o-mini" in str(exc.value)


def test_replay_reproduces_the_recorded_score_exactly(tmp_path):
    """The point of the lab: replay must score identically to the run it replays."""
    recording = find_recording(RECORDINGS, "feat_001", "gemini-2.5-flash")
    recorded = json.loads(recording.read_text())

    row = run_case("feat_001", RecordedProvider(recording), tasks_dir=REPO_ROOT / "tasks",
                   out_file=tmp_path / "rows.jsonl", replayed=True)

    from realdataagentbench.core.registry import TaskRegistry
    from realdataagentbench.scoring.composite import CompositeScorer
    original = CompositeScorer().score(
        TaskRegistry(REPO_ROOT / "tasks").get("feat_001"), recorded
    )
    assert row["scores"]["dab_score"] == original.dab_score
    assert row["scores"]["correctness"] == original.correctness
    assert row["scores"]["stat_validity"] == original.stat_validity
    assert row["tokens"] == (recorded["trace"]["total_input_tokens"]
                             + recorded["trace"]["total_output_tokens"])


def test_every_step_is_recorded_and_serializable(tmp_path):
    recording = find_recording(RECORDINGS, "feat_001", "gemini-2.5-flash")
    row = run_case("feat_001", RecordedProvider(recording), tasks_dir=REPO_ROOT / "tasks",
                   out_file=tmp_path / "rows.jsonl", replayed=True)

    assert [s["step"] for s in row["steps"]] == list(STEP_NAMES)
    json.dumps(row)                                  # the whole row must serialize
    run_model = next(s for s in row["steps"] if s["step"] == "run_model")
    assert run_model["replayed"] is True
    assert run_model["output"]["tokens"] > 0


def test_result_row_is_appended_to_the_artifact(tmp_path):
    recording = find_recording(RECORDINGS, "feat_001", "gemini-2.5-flash")
    out = tmp_path / "nested" / "rows.jsonl"
    for _ in range(2):
        run_case("feat_001", RecordedProvider(recording), tasks_dir=REPO_ROOT / "tasks",
                 out_file=out, replayed=True)
    lines = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
    assert len(lines) == 2
    assert {line["mode"] for line in lines} == {"replayed"}


def test_lab_cli_refuses_live_without_the_env_var(tmp_path, monkeypatch):
    import scripts.kitaru_replay_lab as lab
    monkeypatch.delenv(lab.LIVE_ENV, raising=False)
    code = lab.main(["--tasks", "feat_001", "--model", "gemini-2.5-flash",
                     "--mode", "live", "--out", str(tmp_path)])
    assert code == 2                                  # refused, nothing spent
