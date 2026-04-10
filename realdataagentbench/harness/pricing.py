"""Token pricing — single source of truth for all model costs.

Prices are USD per 1 million tokens (input / output).
Source: official pricing pages as of April 2026.

Both ``harness/providers.py`` and ``scripts/build_leaderboard.py`` import
from here so the numbers never drift out of sync.
"""

from __future__ import annotations

# (input_$/M, output_$/M)
COST_PER_M_TOKENS: dict[str, tuple[float, float]] = {
    # ── Anthropic ─────────────────────────────────────────────────────────────
    "claude-sonnet-4-6":         (3.00,  15.00),
    "claude-opus-4-6":           (15.00, 75.00),
    "claude-haiku-4-5-20251001": (0.25,   1.25),
    # short aliases kept for backwards-compat with old output files
    "haiku":                     (0.25,   1.25),
    # ── OpenAI ────────────────────────────────────────────────────────────────
    "gpt-5":                     (15.00, 60.00),
    "gpt-5-mini":                (1.10,   4.40),
    "gpt-4.1":                   (2.00,   8.00),
    "gpt-4.1-mini":              (0.40,   1.60),
    "gpt-4.1-nano":              (0.10,   0.40),
    "gpt-4o":                    (2.50,  10.00),
    "gpt-4o-mini":               (0.15,   0.60),
    "gpt-4-turbo":               (10.00, 30.00),
    "gpt-4":                     (30.00, 60.00),
    "gpt-3.5-turbo":             (0.50,   1.50),
    # ── Groq (Llama / Mixtral / Gemma) — paid-tier prices ────────────────────
    "llama-3.3-70b-versatile":   (0.59,   0.79),
    "llama-3.1-70b-versatile":   (0.59,   0.79),
    "llama-3.1-8b-instant":      (0.05,   0.08),
    "llama3-70b-8192":           (0.59,   0.79),
    "llama3-8b-8192":            (0.05,   0.08),
    "mixtral-8x7b-32768":        (0.24,   0.24),
    "gemma2-9b-it":              (0.20,   0.20),
    # ── xAI Grok ──────────────────────────────────────────────────────────────
    "grok-3":                    (3.00,  15.00),
    "grok-3-mini":               (0.30,   0.50),
    "grok-3-fast":               (5.00,  25.00),
    "grok-2-1212":               (2.00,  10.00),
    # ── Google Gemini ─────────────────────────────────────────────────────────
    "gemini-2.5-pro":            (1.25,  10.00),
    "gemini-2.5-flash":          (0.15,   0.60),
    "gemini-2.0-flash":          (0.10,   0.40),
    "gemini-2.0-flash-lite":     (0.075,  0.30),
}

# Used when a model isn't in the table — conservative over-estimate.
_FALLBACK_COST: tuple[float, float] = (1.00, 3.00)


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated cost in USD for a given token usage."""
    in_per_m, out_per_m = COST_PER_M_TOKENS.get(model, _FALLBACK_COST)
    return round(
        (input_tokens / 1_000_000) * in_per_m
        + (output_tokens / 1_000_000) * out_per_m,
        6,
    )
