# Show HN: RealDataAgentBench — frontier LLMs score 0.25 on statistical validity while scoring 0.83+ on correctness

**Title (choose one):**

> Show HN: I benchmarked 12 LLMs on data science tasks – they all score ~0.25 on statistical validity while scoring 0.83+ on correctness

> Show HN: RealDataAgentBench – LLM agents get the right answer but skip the uncertainty quantification, every time

---

**Body (196 words):**

I built an open-source benchmark (RDAB) to test whether LLM agents produce statistically sound data science work — not just correct answers.

The finding: every frontier model (GPT-5, GPT-4o, Llama 3.3-70B, Gemini 2.5, Grok-3-mini) scores 0.25 on statistical validity while scoring 0.83–1.00 on correctness on the same tasks. The pattern holds across 12 models and 227 runs. Models compute the right feature importances, fit the right models, pass the correctness check — then stop. No confidence intervals. No acknowledgment that a coefficient ranking might be unstable. No distinction between statistical significance and practical significance.

The benchmark scores four dimensions: correctness, code quality, efficiency, and statistical validity. Each task has ground truth and a reproducible seeded dataset. You can run any model locally with one API key.

Some other numbers that came out:
- Claude Haiku used 608K tokens on a feature engineering task that GPT-4.1 completed in 28K
- grok-3-mini scores zero on every sklearn task due to a namespace adaptation failure
- GPT-4.1-mini leads the leaderboard at 47× lower cost than GPT-5

Live leaderboard: https://patibandlavenkatamanideep.github.io/RealDataAgentBench/
Repo: https://github.com/patibandlavenkatamanideep/RealDataAgentBench

---

*Do not post until README and leaderboard are reviewed.*
