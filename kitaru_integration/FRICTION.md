# Friction log — integrating RDAB with Kitaru

Kitaru 0.26.0, macOS 15 (arm64), Python 3.13, 2026-09-19. Every error below is quoted
verbatim from the terminal. Ordered by how much time each cost.

## Blocking

### 1. No `@flow` / `@checkpoint` in the Python SDK
**Expected:** decorators to wrap an existing function as a flow with checkpoint boundaries.
**Found:** `dir(kitaru)` is empty; no such symbol anywhere in the package. The only Python
integration paths are three framework adapters (`kitaru-pydantic-ai`, `kitaru-langgraph`,
`kitaru-openai-agents`) or a custom **importer** for traces you already have.
**Impact:** an agent built on raw provider SDKs — which RDAB is — cannot be instrumented
natively. We wrote an importer instead. Roughly half a day of redesign.

### 2. Replay cannot resume mid-run, and the docs say so only in prose
> "replays re-run the agent **from the top**. There is no partial, mid-run cut point."
> — core-concepts/replay

**Impact:** the "replay from a checkpoint, measure tokens saved" plan is not achievable.
What replay actually caches is tool results via `--tool-policy history`. For a benchmark
whose tools are local code execution, that saves no money at all. Worth stating on the
replay page next to the tool-policy description, since the economics are the reason most
people reach for replay.

### 3. A custom agent's replay runs the command verbatim, with no documented protocol
Registered `rdab-agent` with `--command "dab run {task_id} --model {model}"`, then:
```
kitaru replay create <session-id> --evaluator stat-validity@latest \
  --tool-policy '{"default":{"type":"history","scope":"baseline","on_miss":"fail"}}'
```
```
replay status: failed
error: "Agent process exited with code 1.
stdout tail: Running {task_id} (model={model}, dry_run=False, runs=1)"
```
The placeholders are never substituted. Reading `kitaru/worker/handlers/agent.py` shows the
real contract: the command runs as-is with `KITARU_TASK_INPUTS` (JSON) and `KITARU_REPLAY_ID`
in the environment. **None of that is in the docs.** `adapters/custom.md` defers to the
PydanticAI adapter as "the reference implementation" — whose `capability` module is 1,084
lines against `KitaruAPIClient`, tool-policy config types and node construction.
**Impact:** replaying a non-framework agent is a project, not an integration step. A short
page listing the env vars and the expected result shape would change that.

## Wrong or missing documentation

### 4. Install docs promise Podman; the CLI hard-requires Docker
installation.md: *"Local server: Docker with Compose v2 plugin, or Podman with Compose support"*.
With the Podman VM running and `DOCKER_HOST` pointed at its socket:
```
{"ok":false,"error":{"kind":"invalid_configuration",
 "message":"Docker with Compose v2 is required to run Kitaru locally.",
 "hint":"Install Docker from https://docs.docker.com/get-docker/, or use Kitaru Cloud..."}}
```
**Workaround that worked:** `brew install docker docker-compose`, add
`"cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"]` to `~/.docker/config.json`,
export `DOCKER_HOST` to the Podman socket. Docker CLI 29.8.1 then drives Podman fine and
`kitaru login --local` succeeds in 27s. So Podman *does* work — the check just looks for
Docker specifically.

### 5. Doc types don't match SDK types
The custom-importer page describes `ParsedSession` / `ParsedNode`. The scaffold that
`kitaru importer scaffold` generates imports `ImportedSession` / `ImportedNode` from
`kitaru.task.importer`. Same concept, different names; the scaffold is correct.

### 6. `GETTING_STARTED.md` does not exist
Referenced in our brief and a natural first guess; the repo root has `AGENTS.md` and
`CLAUDE.md`, and a code search for the filename returns nothing.

### 7. Install extra in circulation is wrong
`uv pip install "kitaru[local]"` fails — there is no `local` extra. PyPI declares
`cli, examples, mcp, modal, otel, s3, server, worker`; the docs use `kitaru[cli,mcp,worker]`.
`--local` is a flag on `kitaru login`, which is probably where the confusion starts.

## Inconsistencies

### 8. The same flag takes different reference formats
`session import --agent` requires `AGENT@VERSION`:
```
*  --agent   Exact AGENT@VERSION reference. [required]
```
`cohort create --agent` requires a UUID or bare name, and rejects the other form with a
misleading error:
```
$ kitaru cohort create rdab-low-validity --agent rdab-agent@latest
{"kind":"not_found","message":"Agent 'rdab-agent@latest' was not found."}
$ kitaru cohort create rdab-low-validity --agent 01a0b5f6-4310-...   # works
```
The agent plainly exists. "Not found" should say "expected a UUID or name, got a versioned
reference".

### 9. List commands disagree on the page-size flag
`session list --limit 30` works. `evaluation list --limit 30` returns
`{"kind":"invalid_arguments","message":"Unknown option: --limit."}` — it wants `--size`.

### 10. Plugin test timeout is 10s with no hint
```
{"ok":false,"error":{"kind":"timeout","message":"Local plugin test exceeded 10 seconds.",
 "details":{"stdout":"","stderr":""}}}
```
The evaluator imported `realdataagentbench`, which pulls pandas and sklearn, and that alone
exceeded the budget. There *is* a `--timeout` flag; the error does not mention it, and
empty stdout/stderr gives nothing to debug. Fixed by importing lazily inside `evaluate()`,
which is better practice anyway — but the error should point at the flag.

### 11. Metadata keys containing "token" are silently redacted
Our importer put `total_input_tokens: 5486` in session metadata. Kitaru stored `"***"`.
The structured `tokens` field is untouched, so nothing was lost, but a numeric count being
redacted as a secret is surprising and undocumented.

### 12. A worker is required even to import
`kitaru session import --wait` times out against a fresh install:
```
{"kind":"timeout","message":"Timed out waiting for job ...; remote work continues.",
 "hint":"Start a worker with `kitaru worker start`, or keep waiting with `kitaru job watch`"}
```
The hint is excellent. Worth saying on the import page that a worker is a prerequisite for
imports, not only for replays.

## Credit where due

- **`kitaru doctor` is the best thing in the CLI.** It caught `~/.config/kitaru has mode
  0o755; expected 0o700` before that broke anything, and emits machine-readable JSON.
- **Every command returns structured JSON** with `ok`, `error.kind`, `hint` and
  `next_actions`. Scripting against it was easy, and `next_actions` repeatedly told us the
  exact next command.
- **The scaffold commands** (`importer scaffold`, `evaluator scaffold`) are the fastest way
  to learn the real contract, and were more accurate than the prose docs.
- **Imported sessions are enriched automatically** — `llm_call_count`, `tool_call_count`
  and structured token usage appeared without us mapping them.
- **The worker never sees your credentials leave the machine**, which made a public demo
  straightforward.

## Found while testing cohorts (Phase 4)

### 13. `--add-session` takes exactly one value, and says so unhelpfully
"Ordered session IDs to add" reads as plural. Both plural forms fail:
```
$ kitaru cohort version create c --add-session ID1 --add-session ID2
{"kind":"invalid_arguments","message":"Unused Tokens: ['ID2']."}
$ kitaru cohort version create c --add-session ID1,ID2
{"kind":"invalid_arguments","message":"Invalid value for --add-session: unable to convert \"ID1,ID2\" into UUID."}
```
Building a four-session cohort therefore takes four commands, each chaining off the
previous version's UUID. "Unused Tokens" also reads like an internal parser message rather
than "this flag accepts one value".

### 14. `--baseline` rejects the reference format its sibling accepts
`cohort version get` accepts `COHORT@VERSION` — that is how it is documented, and it works.
`cohort version create --baseline` does not:
```
{"kind":"invalid_arguments","message":"Invalid value for --baseline: unable to convert \"rdab-low-validity@1\" into UUID."}
```
Third place in this CLI where the same style of reference means different things:
`session import --agent` wants `NAME@VERSION`, `cohort create --agent` wants a UUID or bare
name, `cohort version create --baseline` wants a UUID only.

### Not a bug, worth recording
`cohort version get` returns `session_count`, not a member list. An earlier note here
claimed the cohort was empty; that was a wrong key guess on our side. `session_count: 4`
confirms the membership is correct.
