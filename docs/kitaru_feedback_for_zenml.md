# Notes on trying Kitaru with an agent benchmark

Written after wrapping a slice of [RealDataAgentBench](https://github.com/patibandlavenkatamanideep/RealDataAgentBench)
with Kitaru 0.26.0, running locally. Everything below is from that attempt rather than from
reading the docs, and the numbers are reproducible from the repo.

## What I tried

RDAB runs LLM agents against realistic data-science tasks: each run is a multi-step loop
where the model writes pandas/sklearn code, a sandbox executes it, and four scorers grade
the final answer (correctness, code quality, efficiency, statistical validity).

I imported 20 real runs as Kitaru sessions, registered RDAB's statistical-validity scorer
as a Kitaru evaluator, used it to find cases that were *correct but statistically weak*,
changed a prompt, and compared the result against the baseline population.

## Why this was a reasonable test case

Benchmark runs look a lot like the production agent sessions Kitaru targets: multi-step,
tool-using, expensive, and worth re-examining after a change. They also have something
production traces usually lack — a ground-truth score — so "did the change help?" has an
answer that is not a matter of opinion.

## What worked well

- **The importer contract is clean.** `parse(payload, params) -> Iterator[ImportedSession]`
  took about an hour to map onto our trace format, and `kitaru importer test` caught my
  mistakes before anything reached the server.
- **Sessions are enriched on arrival.** `llm_call_count`, `tool_call_count` and structured
  token usage appeared without my mapping them.
- **Evaluators are the feature I would actually keep.** Wrapping our existing scorer meant
  Kitaru and our CLI agreed exactly on all 20 sessions, and because the evaluator returns
  an explanation, a low score says *which* check failed:
  `uncertainty=0.0 method=False interpretation=False`. That is what made the fix targeted
  rather than guesswork — mean validity went 0.375 → 0.812 with correctness unchanged.
- **`kitaru doctor`** caught a config permissions problem before it could fail anything.
  Structured JSON on every command, with `hint` and `next_actions`, made scripting easy.
- **Local-first actually works.** The worker runs our code, so no prompts or keys left the
  machine — which matters for publishing the experiment.

## What was confusing

1. **The install docs list Podman as supported; the CLI rejects it.**
   `"Docker with Compose v2 is required to run Kitaru locally."` with a Podman VM running
   and `DOCKER_HOST` set. Installing the Docker *CLI* and pointing it at the Podman socket
   works fine, so the capability is there — the check just looks for Docker specifically.

2. **The custom-agent replay protocol is undocumented.** I registered an agent, called
   `kitaru replay create`, and the worker ran my command verbatim with placeholders
   unsubstituted. The real contract turned out to be `KITARU_TASK_INPUTS` and
   `KITARU_REPLAY_ID` in the process environment, which I found in
   `worker/handlers/agent.py`. `adapters/custom.md` points at the PydanticAI adapter as the
   reference implementation, and that file is 1,084 lines — which reads as "port your agent
   to a supported framework" rather than "here is the interface".

3. **"Replay" means something different to benchmark people.** Coming from evals, replay
   suggests *cached* — skip the expensive part. Kitaru re-runs the agent from the top and
   caches tool results. That is the right design for agents whose tools hit real systems,
   but for us the expense is model tokens and the tools are free local code execution, so
   replay costs full price. The docs say this plainly in one line; it deserves to be next
   to the tool-policy description, because it determines whether replay saves anyone money.

4. **Reference formats differ between commands.** `session import --agent` wants
   `NAME@VERSION`; `cohort create --agent` wants a UUID or bare name and rejects
   `NAME@VERSION` with "not found"; `cohort version create --baseline` wants a UUID and
   rejects `COHORT@VERSION`, which its sibling `cohort version get` accepts. Each mismatch
   surfaced as a "not found" rather than "wrong format", which made them slow to diagnose.

5. **Small ones:** `evaluation list` takes `--size` where `session list` takes `--limit`;
   `--add-session` accepts exactly one value while reading as plural; the 10s plugin-load
   timeout does not mention its own `--timeout` flag; and metadata keys containing "token"
   are silently redacted to `***` (our token counts, not secrets).

## What I would find most useful next

1. **A one-page custom-agent contract** — the env vars, the expected result shape, and a
   30-line example. This is the difference between "adapters exist for three frameworks"
   and "any agent can participate".
2. **A line on the replay page about cost**, saying that model calls re-execute and tool
   results are what gets reused.
3. **Consistent reference parsing**, or errors that name the expected format.
4. **Optional:** a `--dry-run` for `replay create` that reports what would be re-executed
   and what would be served from history, before spending anything.

## Where this connects to reproducibility receipts

I maintain [EvalSeal](https://pypi.org/project/evalseal/), which records an eval's runs into
a hash-linked, signed ledger with a request/response cassette, so a result can be replayed
with no API key and verified later. The overlap with Kitaru is real and the emphasis is
different: EvalSeal is about *proving a past result*, Kitaru is about *testing a change
against past behaviour*.

The gap I ran into sits between them. Kitaru holds the sessions and the judgment; it cannot
re-run my agent. My cassette can serve a run offline; it has no notion of cohorts,
evaluators or experiments. In this experiment I bridged that with a small recorded provider
inside RDAB — replaying two tasks in 0.05s each at $0, reproducing the DAB scores exactly.
That bridge is 80 lines, which suggests the missing piece on Kitaru's side is small too:
a documented way for an arbitrary Python agent to accept a replayed input and report a
session back.

Happy to share the branch, the importer, or the evaluator if any of it is useful — and
equally happy to be told I approached the replay model the wrong way round.
