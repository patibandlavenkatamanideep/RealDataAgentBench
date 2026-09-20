"""Kitaru evaluator wrapping RDAB's StatValidityScorer.

The scorer is imported unchanged from the benchmark, so a Kitaru evaluation and a
`dab score` scorecard agree by construction. It reads the session's final answer and
the task category (both carried by the importer) and reports the four sub-checks —
uncertainty, method vocabulary, interpretation, p-hacking — as the explanation, so a
low score says *which* check failed rather than only that it failed.
"""

from __future__ import annotations

from typing import Any

from kitaru.task.evaluator import EvaluationResult, SessionView

# Imported lazily inside evaluate(): pulling RDAB at module scope drags in pandas and
# sklearn, which blows Kitaru's 10-second plugin-load budget on a cold filesystem.


def _final_answer(session: SessionView) -> str:
    outputs = getattr(session.session, "outputs", None) or {}
    if isinstance(outputs, dict):
        for key in ("final_answer", "text", "output"):
            if isinstance(outputs.get(key), str):
                return outputs[key]
    # Fall back to the last assistant node's text.
    for node in reversed(session.nodes):
        node_outputs = getattr(node, "outputs", None) or {}
        if isinstance(node_outputs, dict) and isinstance(node_outputs.get("text"), str):
            return node_outputs["text"]
    return ""


def _category(session: SessionView, params: dict[str, Any]) -> str:
    if params.get("category"):
        return str(params["category"])
    meta = getattr(session.session, "metadata", None) or {}
    return str(meta.get("category") or "eda")


def evaluate(session: SessionView, **params: Any) -> EvaluationResult:
    """Score one session's final answer for statistical validity (0.0–1.0)."""
    try:
        from realdataagentbench.scoring.stat_validity import StatValidityScorer
    except ModuleNotFoundError as exc:
        return EvaluationResult(
            name="stat_validity",
            passed=False,
            explanation=f"realdataagentbench not importable in the worker: {exc}",
        )

    answer = _final_answer(session)
    category = _category(session, params)
    threshold = float(params.get("threshold", 0.5))

    detail = StatValidityScorer().score_detailed(answer, category=category)
    checks = (
        f"uncertainty={detail.reports_uncertainty} "
        f"method={detail.uses_appropriate_test} "
        f"interpretation={detail.interprets_correctly} "
        f"no_p_hacking={detail.avoids_p_hacking_signals}"
    )
    return EvaluationResult(
        name="stat_validity",
        score=detail.score,
        min_score=0.0,
        max_score=1.0,
        target_score=threshold,
        passed=detail.score >= threshold,
        explanation=(
            f"category={category} answer_chars={len(answer)} | {checks}"
            if answer else f"category={category} | empty final answer"
        ),
    )
