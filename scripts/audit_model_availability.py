"""Check every model in the registry against the providers' live model lists.

A leaderboard row is only meaningful if the same command still runs today. Two things
break that without touching this repo: a provider retires a model, or a provider SDK
changes a parameter the harness still sends. This script reports both.

    python scripts/audit_model_availability.py

Uses only free list-models endpoints — no generation, no cost. Providers without a key
configured are reported as "unchecked" rather than counted either way.
"""

from __future__ import annotations

import collections
import json
import os
import pathlib
import sys

import httpx
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

from realdataagentbench.harness.providers import (  # noqa: E402
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
    GROK_MODELS,
    GROQ_MODELS,
    MODEL_ALIASES,
    OLLAMA_MODELS,
    NO_SAMPLING_PARAM_MODELS,
    OPENAI_MODELS,
)

ENDPOINTS = {
    "Anthropic": ("ANTHROPIC_API_KEY", "https://api.anthropic.com/v1/models?limit=100",
                  lambda k: {"x-api-key": k, "anthropic-version": "2023-06-01"}),
    "OpenAI": ("OPENAI_API_KEY", "https://api.openai.com/v1/models",
               lambda k: {"Authorization": f"Bearer {k}"}),
    "Groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1/models",
             lambda k: {"Authorization": f"Bearer {k}"}),
    "Google": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/models",
               lambda k: {"Authorization": f"Bearer {k}"}),
    "xAI": ("XAI_API_KEY", "https://api.x.ai/v1/models",
            lambda k: {"Authorization": f"Bearer {k}"}),
}
REGISTRY = {
    "Anthropic": ANTHROPIC_MODELS, "OpenAI": OPENAI_MODELS, "Groq": GROQ_MODELS,
    "Google": GEMINI_MODELS, "xAI": GROK_MODELS,
    # Ollama models are served by a local daemon, not a hosted API, so there is no
    # list endpoint to check here; they are reported as unchecked.
    "Ollama": OLLAMA_MODELS,
}


def harness_can_call_anthropic(model: str) -> bool:
    """Would this harness successfully build an Anthropic request for `model` today?

    The failure this catches is real but subtle: anthropic>=1.0 removed `temperature`
    from messages.create(), and a harness that sends it unconditionally dies with a
    TypeError before any request goes out. Ask the installed SDK and the harness's own
    rule rather than assuming either.
    """
    import inspect

    import anthropic

    if model in NO_SAMPLING_PARAM_MODELS:
        return True                      # the harness never sends the parameter here
    accepts = "temperature" in inspect.signature(
        anthropic.Anthropic(api_key="probe").messages.create
    ).parameters
    if accepts:
        return True                      # SDK still takes it
    # SDK dropped it: fine only if the harness asks the SDK before sending.
    from realdataagentbench.harness import providers
    return hasattr(providers.AnthropicProvider, "__init__") and "_sdk_accepts_temperature" in (
        inspect.getsource(providers.AnthropicProvider)
    )


def live_models(provider: str) -> set[str] | None:
    """Model ids the provider serves this key, or None when unchecked."""
    if provider not in ENDPOINTS:      # e.g. Ollama: a local daemon, no hosted list API
        return None
    env_var, url, headers = ENDPOINTS[provider]
    key = os.environ.get(env_var)
    if not key:
        return None
    try:
        response = httpx.get(url, headers=headers(key), timeout=30)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        print(f"  {provider}: could not check ({type(exc).__name__})", file=sys.stderr)
        return None
    payload = response.json()
    entries = payload.get("data") or payload.get("models") or []
    # Google returns "models/gemini-2.5-flash"; everyone else returns a bare id.
    return {(m.get("id") or m.get("name") or "").split("/")[-1] for m in entries}


def main() -> None:
    root = pathlib.Path(__file__).resolve().parent.parent
    runs = json.loads((root / "docs/results.json").read_text())["runs"]
    counts = collections.Counter(r["model"] for r in runs)
    # Only drop shortcuts that point at a different id; "gemma4" -> "gemma4" is a real
    # model name that happens to also be its own alias.
    aliases = {short for short, target in MODEL_ALIASES.items() if short != target}

    buckets: dict[str, list] = {"retired": [], "sdk_blocked": [], "ok": [], "unchecked": []}
    for provider, models in REGISTRY.items():
        available = live_models(provider)
        for model in sorted(models - aliases):
            n = counts.get(model, 0)
            row = (model, provider, n)
            if available is None:
                buckets["unchecked"].append(row)
            elif model not in available:
                buckets["retired"].append(row)
            elif provider == "Anthropic" and not harness_can_call_anthropic(model):
                buckets["sdk_blocked"].append(row)
            else:
                buckets["ok"].append(row)

    titles = {
        "retired": "RETIRED at the provider",
        "sdk_blocked": "LIVE, but the installed SDK rejects the call",
        "ok": "REPRODUCIBLE today",
        "unchecked": "UNCHECKED (no key configured, or a local runtime)",
    }
    totals = {}
    for bucket, rows in buckets.items():
        n_runs = sum(r[2] for r in rows)
        totals[bucket] = n_runs
        print(f"\n{titles[bucket]} — {len(rows)} models, {n_runs} leaderboard runs")
        for model, provider, n in sorted(rows, key=lambda r: -r[2]):
            if n:
                print(f"    {model:30} {provider:10} {n:4} runs")

    total = sum(counts.values())
    blocked = totals["retired"] + totals["sdk_blocked"]
    print(f"\ntotal leaderboard runs: {total}")
    print(f"  blocked:      {blocked:4} ({blocked / total:.0%})")
    print(f"  reproducible: {totals['ok']:4} ({totals['ok'] / total:.0%})")
    print(f"  unchecked:    {totals['unchecked']:4} ({totals['unchecked'] / total:.0%})")

    if "--check" in sys.argv:
        # CI mode: fail only on a model that has recorded runs and was actually checked.
        # An unconfigured provider is unchecked, not broken, and must not fail the build.
        offenders = [r for r in buckets["retired"] + buckets["sdk_blocked"] if r[2] > 0]
        if offenders:
            print("\nFAIL: models with recorded leaderboard runs can no longer be run:")
            for model, provider, n in sorted(offenders, key=lambda r: -r[2]):
                print(f"  {model} ({provider}) — {n} recorded runs")
            print("Update the registry or the harness, then refresh docs/results.json.")
            raise SystemExit(1)
        print("\nOK: every checked model with recorded runs is still callable.")


if __name__ == "__main__":
    main()
