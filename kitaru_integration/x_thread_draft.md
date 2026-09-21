# Draft X thread (7 posts)

Every number here was measured in this repo on 2026-09-19. Nothing is extrapolated.
Written for: people who run LLM benchmarks or evals.

---

**1/**
I wired my LLM data-science benchmark (RealDataAgentBench) into Kitaru to find where
models are *right but not rigorous*.

Before I found anything about models, the benchmark told on itself: two of the three
models in my leaderboard can't run today.

---

**2/**
`claude-sonnet-4-6`: every run died instantly.

```
Messages.create() got an unexpected
keyword argument 'temperature'
```

The SDK dropped `temperature`. My harness still sent it. 0 steps, 0 tokens — every Claude
row in my leaderboard unreproducible.

---

**3/**
`llama-3.3-70b-versatile`: 404, `model_not_found`.

Groq has retired every Llama model my registry knows about. 39 recorded runs I cannot
reproduce with the same command.

Benchmarks don't rot because the code changed. They rot because providers move.

---

**4/**
Once running: 3 tasks × 3 models → Kitaru sessions, scored by my own stat-validity scorer
registered as a Kitaru evaluator.

It names *which* check failed:

`uncertainty=0.0 method=False interpretation=False`

4 cases: correct (1.00), statistically weak (≤0.50).

---

**5/**
The fix: one prompt addendum asking for quantified uncertainty, named methods, and stated
limitations. Not the scorer's keywords — that would game a lexical scorer instead of
improving the analysis.

Mean stat_validity **0.375 → 0.812**. Correctness held at 1.00 in all four.

---

**6/**
The average hides this:

• gemini-2.5-flash: 0.25 → 1.00 on **fewer** tokens (7.4k → 5.2k)
• claude-sonnet-4-6: 0.50 → 1.00 but 4× tokens ($0.21 → $0.74); composite score *fell*
• gpt-4o-mini: 0.50 → 0.50, 2.9× tokens, zero gain

Same prompt. Three outcomes.

---

**7/**
One expectation I dropped: replay-from-checkpoint to save tokens.

Kitaru replays re-run from the top. What it caches is *tool results* — mine are local code
execution, so that buys determinism, not money.

Write-up + 12-item friction log: [link]
Total spend: $1.80
