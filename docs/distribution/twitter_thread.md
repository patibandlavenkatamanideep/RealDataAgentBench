# Twitter / X thread

**6 tweets. Do not post until README and leaderboard are reviewed.**

Character counts are noted. Twitter limit is 280 per tweet.

---

**Tweet 1 — The paradox (hook)**

> Frontier LLMs score 0.83–1.00 on correctness on data science tasks.
>
> The same models score 0.25 on statistical validity on the same tasks.
>
> Every single one. GPT-5, Claude, Llama, Gemini, Grok. All of them.
>
> Here's what that actually means 🧵

*(248 chars)*

---

**Tweet 2 — Failure pattern 1: correct number, wrong reasoning**

> A model fits a logistic regression. Correctly identifies the top feature. Reports accuracy 0.74 and AUC 0.84.
>
> Then stops.
>
> No CI on the AUC. No note that the coefficient ranking may shift across splits. No uncertainty.
>
> Correctness: 1.0. Stat validity: 0.25.
>
> [screenshot placeholder: model_001 scorecard showing correctness=1.0, stat_validity=0.25]

*(271 chars without placeholder)*

---

**Tweet 3 — Failure pattern 2: token spiral**

> Claude Haiku used 608,861 tokens on a feature engineering task.
>
> GPT-4.1 completed the same task in 28,000 tokens with higher correctness.
>
> The Anthropic models explore more. They conclude less efficiently. Efficiency score: 0.13.
>
> Exploration ≠ efficiency.
>
> [screenshot placeholder: efficiency comparison bar chart feat_005]

*(263 chars without placeholder)*

---

**Tweet 4 — Failure pattern 3: hard capability gaps**

> grok-3-mini scores 0.00 on 7 of 23 tasks. Every single one involves sklearn.
>
> The model tries to import sklearn inside the sandbox, hits the restriction, retries, gives up. Never adapts to the pre-injected namespace.
>
> Aggregate score: 0.63. Hidden failure mode: complete.
>
> [screenshot placeholder: grok-3-mini task breakdown showing bimodal correctness]

*(272 chars without placeholder)*

---

**Tweet 5 — Cost-performance finding**

> GPT-4.1-mini leads the leaderboard (RDAB score 0.832).
>
> Cost: $0.013/task.
>
> GPT-5 scores 0.812 — 2.4% lower — at $0.596/task.
>
> That's 47× more expensive for the #2 spot.
>
> GPT-4.1 scores within 3% of GPT-5 at 15× lower cost.
>
> The best model for your use case is rarely the most expensive one.

*(272 chars)*

---

**Tweet 6 — Link and invitation**

> I built this to answer a question I kept running into: LLMs get the right answer, but do they reason correctly?
>
> 227 runs, 12 models, 23 tasks, open source.
>
> Leaderboard + full methodology (including scorer limitations): [URL]
>
> Would genuinely appreciate feedback from anyone who runs it.

*(278 chars — replace [URL] with actual link before posting)*

---

## Notes for posting

- Post tweets as a thread in sequence; the first tweet carries the hook
- Attach the scorecard screenshot to tweet 2 (model_001: correctness=1.0, stat_validity=0.25) — this is the most visually striking single image
- If engagement is strong on tweet 1, consider quote-tweeting with the methodology doc link once the thread has traction
- Do not post all six at once if scheduling — the first tweet is the anchor; others can follow within minutes
- Replace [URL] in tweet 6 with the live leaderboard URL before posting
