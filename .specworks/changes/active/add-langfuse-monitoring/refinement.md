# Refinement: add-langfuse-monitoring

## Problem

Nobody using specworks can see how its skills perform: which phases fail their
gates, how many build cycles or review findings a change takes, how long each
phase runs, or what the agent spends (tokens, cost, latency) per skill. Without
that, improving the skills is guesswork. Langfuse is the chosen place to look at
this data.

## Outcomes

- Each specworks change shows in Langfuse as one trace named by its `ref`, with
  a span per CLI step (phase start, gate pass/fail, run result, review findings,
  validate PASS/FAIL, commit, close) carrying its duration and result.
- Phases and skills can be filtered and compared across changes (e.g. which
  phase fails its gate most, how many build cycles a change takes).
- When the agent exports its own telemetry, its token/cost/latency data for the
  same session can be linked to that change's trace.
- With Langfuse not enabled, specworks behaves exactly as today; with it enabled
  but unreachable, no command fails or is noticeably slower.
- No code, spec text or prompt content leaves the machine unless explicitly
  enabled: only names, IDs, counts, durations and results.

## Context

**Observed:**
- No telemetry exists anywhere in the repo; the only external process specworks
  talks to is git.
- `project` (`src/specworks/core`) owns changes and phases: `set_phase` in
  `core/changes.py` moves a change between phases, `commit_phase` commits at
  each phase boundary, and each change has a stable `ref` and `created`
  timestamp in its metadata.
- `workflow` (`src/specworks/workflow`) owns gates, review findings, build
  cycles and validate; `project` runs the test/lint commands with result reuse.
- `integrations` (`src/specworks/tools`) is where specworks talks to outside
  tools (D2, Claude Code, Copilot).
- `.specworks/config.yml` is committed and edited with `specworks config set`.
- The skills run inside the agent; specworks only sees the CLI calls they make.

**Assumed:**
- Claude Code's OpenTelemetry export sends metrics and log events (tokens, cost,
  tool calls) rather than traces, and Langfuse's OTLP endpoint takes traces, so
  agent data may need a collector or a join rather than direct nesting.
- Copilot's ability to export telemetry is unknown.
- Langfuse's public ingestion API accepts batched trace/span events with basic
  auth from the public/secret key pair.

## Constraints

- [hard] Keys never go in `.specworks/config.yml` or any committed file, and are
  never printed; they come from `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
  (and `LANGFUSE_HOST`).
- [hard] Sending happens only when the project opted in (a non-secret
  `telemetry:` block in config.yml) and keys are set.
- [hard] Off by default; an unreachable Langfuse never fails a command.
- [hard] No content (code, spec text, prompts) is sent by default.
- [hard] Works on Linux, Windows and macOS; text files read/written as UTF-8.
- [soft] No new runtime dependency; the wheel stays small.
- [soft] Commands stay as fast as today.

## Options

### Option A: Langfuse SDK, sent inline

An optional extra `specworks[langfuse]`; each command creates spans with the
Langfuse SDK and flushes them on exit.

- **Pros:** least code; SDK handles batching and the API.
- **Cons:** every command waits on a network flush; a dependency tied to one
  vendor.
- **Effort:** S
- **Touches:** `integrations`, `project`, `workflow`, `cli`
- **Outcomes:** meets 1, 2, 5; 3 via IDs; fails 4 (slowdown on each command).

### Option B: OpenTelemetry to Langfuse's OTel endpoint

An optional extra with the OTel SDK and OTLP exporter, sending spans to
Langfuse's OTLP endpoint.

- **Pros:** vendor-neutral; same model the agent exports in, best for linking.
- **Cons:** heavier dependencies; same per-command flush cost as A.
- **Effort:** M
- **Touches:** `integrations`, `project`, `workflow`, `cli`
- **Outcomes:** meets 1, 2, 5, best at 3; fails 4.

### Option C: Local event log, sent at phase boundaries

The CLI appends JSONL events to the change folder (stdlib only). `commit` and
`close` send unsent events to Langfuse's ingestion API with a short timeout;
`specworks telemetry push` retries what is left.

- **Pros:** commands only write a local file; no new dependency; the log is
  useful offline and can be inspected before it is sent.
- **Cons:** specworks owns a small client for Langfuse's documented ingestion
  API; data arrives per phase, not live.
- **Effort:** M
- **Touches:** `project` (event log), `integrations` (Langfuse client),
  `workflow` (events from gates, review, validate), `cli` (`telemetry push`,
  status)
- **Outcomes:** meets 1, 2, 4, 5; 3 via IDs.

## Recommendation

Option C, agreed with the user. It is the only option that meets outcome 4 for
a CLI made of many short commands, and it adds no dependency. Configuration:
keys from environment variables, the opt-in and host in a `telemetry:` block of
config.yml, shown in `context`/`status` only as on/off and host.

## Open Questions

- How agent telemetry joins a change: by time window, or by setting a
  `specworks.change` attribute in the agent session (who can answer: the
  developer, by checking Claude Code's OTel export against Langfuse during
  specify).
- Whether Copilot can export telemetry at all (who can answer: the developer,
  from Copilot's docs).

## Candidate Capabilities

- `project`: modified - the per-change event log and the `telemetry:` config block.
- `integrations`: modified - the Langfuse client that sends the log.
- `workflow`: modified - gates, review, cycles and validate record events.
- `cli`: modified - `specworks telemetry push` and on/off in `context`/`status`.
