# r/MachineLearning post

**Flair:** Project

**Title:**
> [Project] I benchmarked 12 LLMs on 23 data science tasks — they all score ~0.25 on statistical validity while scoring 0.83+ on correctness on the same tasks

---

**Body:**

I've been working on RealDataAgentBench (RDAB), an open-source benchmark for evaluating whether LLM agents produce statistically sound data science work — not just correct answers.

**The central finding:**

Every model in the benchmark — GPT-5, GPT-4o, GPT-4.1, Llama 3.3-70B, Gemini 2.5 Flash, Grok-3-mini, Claude Opus — scores 0.25 on statistical validity on modeling and feature-engineering tasks while scoring 0.83–1.00 on correctness for the same tasks. Not some models. All of them.

What this means concretely: an agent fits a logistic regression, correctly identifies glucose as the top predictor with the right coefficient (1.17), reports accuracy 0.74 and ROC-AUC 0.84 — and never mentions that these are estimates from a single 160-sample test split, never reports a confidence interval on the AUC, never notes that the coefficient ranking may not be stable. The correctness scorer passes it. The statistical validity scorer gives it 0.25.

**Benchmark design:**

- 23 tasks across EDA, feature engineering, modeling, statistical inference, and ML engineering
- 4-dimensional scoring: correctness, code quality, efficiency, statistical validity
- Reproducible seeded dataset generators — no external downloads, no API needed for the test suite
- Tracks cost per run; most tasks complete in <$0.05 for mid-tier models
- 7 models at full 23/23 coverage; 5 partial-coverage models excluded from ranking

**Some other findings from 227 runs:**

*Failure pattern 1 — Correct number, wrong reasoning:*
On `feat_002`, `feat_003`, `model_001–003`, every model computes the right feature importances or coefficients, then stops. No model spontaneously adds: which features are statistically indistinguishable, whether the importance ranking is stable across folds, or whether the model is overfit. Correctness = 1.0, Stat Validity = 0.25.

*Failure pattern 2 — Token spiral:*
Claude Haiku used 608,861 tokens on `feat_005` (efficiency score: 0.13). Claude Sonnet used 375,920 on `feat_004`. GPT-4.1 completed the same tasks in under 30K tokens with higher correctness. The Anthropic models explore more but conclude less efficiently.

*Failure pattern 3 — Namespace adaptation failure:*
grok-3-mini scores zero on 7 of 23 tasks — every one involving sklearn. The model attempts to import sklearn inside the sandboxed code runner, hits the restriction, then retries rather than adapting to the pre-injected namespace. Its 0.626 overall score hides a bimodal distribution: near-perfect on EDA, zero on anything requiring a trained model.

*Failure pattern 4 — Output truncation:*
Gemini 2.5 Flash produces structurally correct code but truncates its final answer before reporting key metrics on `mod_003`, `model_002`, and `feat_005`. Average correctness 0.58 despite reaching the right intermediate steps.

**Cost-performance:**

GPT-4.1-mini leads the full-coverage leaderboard (RDAB score 0.832) at $0.013/task — 47× cheaper than GPT-5 ($0.596/task, score 0.812). GPT-4.1 scores within 3% of GPT-5 at 15× lower cost. Llama 3.3-70B via Groq scores 0.772 at $0.002/task.

**Honest caveats:**

The statistical validity scorer is lexical — it checks for the presence of uncertainty language, not whether the uncertainty is correctly quantified. It has a known bug where the "appropriate test" check only recognises EDA vocabulary regardless of task category, which imposes a floor of 0.25 on non-EDA tasks even when the method is appropriate. The finding that models skip uncertainty language is real; the absolute 0.25 floor is partly scorer-imposed. Full methodology and a worked manual re-score are in the repo.

5 of 12 models have partial task coverage and are excluded from ranking. Their averages are not directly comparable to full-coverage models.

**Links:**

- Repo: https://github.com/patibandlavenkatamanideep/RealDataAgentBench
- Live leaderboard: https://patibandlavenkatamanideep.github.io/RealDataAgentBench/
- Scorer methodology: [docs/methodology/stat_validity.md](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/blob/main/docs/methodology/stat_validity.md)

Happy to answer questions about the task design, scoring methodology, or specific model behaviors.

---

*Do not post until README and leaderboard are reviewed. Check r/MachineLearning sidebar for current self-promotion rules before posting — the project flair typically requires framing around findings, not the tool itself.*
