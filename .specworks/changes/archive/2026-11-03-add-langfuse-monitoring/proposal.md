# Proposal: add-langfuse-monitoring

## Why

Nobody can see how the specworks skills perform across changes: which gates
fail, how many review findings and build cycles a change takes, or how long
each phase runs. Sending what the CLI already knows to Langfuse, without
slowing or breaking any command, makes that visible (option C of the
refinement).

## What Changes

- A new top-level config block `telemetry:` with `langfuse` (true/false) and
  an optional `host`; refused in a module's config, like `tools`. Settable with
  `specworks config set telemetry.langfuse true` and `telemetry.host <url>`.
- With `telemetry.langfuse: true`, the commands that act on a change (`new`,
  `phase`, `start`, `gate`, `run`, `finding`, `cycle`, `validate`, `commit`,
  `close`, `abandon`) append one JSON line per event to `events.jsonl` in the
  change's folder: only names, IDs, counts, durations and results. A
  `.gitignore` in the change folder keeps the log (and its sent marker) out of
  git. With telemetry off, nothing is written.
- `specworks commit` sends the change's unsent events to Langfuse's public
  ingestion API, with a short timeout, after committing; a failure never fails
  the commit, and the events stay queued.
- A new `specworks telemetry push --change <ref>` sends what is still queued,
  and reports why when it cannot.
- Keys come only from `SPECWORKS_LANGFUSE_PUBLIC_KEY` and
  `SPECWORKS_LANGFUSE_SECRET_KEY`; `SPECWORKS_LANGFUSE_HOST` overrides the
  config's host. The plain `LANGFUSE_*` variables are ignored, so a project's
  own Langfuse keys never receive specworks data. Keys are never written or
  printed.
- Each change has a stable trace ID (from its module, name and creation time)
  and a session ID (its ref): sent with every event, and shown by
  `status --json`, so agent telemetry can later be joined to it.
- `context` shows whether telemetry is on, its host, and whether the keys are
  set (never their values).

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `project`: the `telemetry:` config block (value checks, `config set`) and
  the per-change event log with its trace identity.
- `integrations`: the Langfuse client: settings from the environment and the
  config, and sending a change's unsent events.
- `cli`: which commands record which events, sending at `commit`,
  `telemetry push`, and telemetry in `context` and `status`.

## Related requirements

- REQ-PROJ-002 left: `telemetry` becomes a known key; the rule (unknown keys are refused) is unchanged.
- REQ-PROJ-003 modified: the shape of `telemetry`, and refusing it in a module's config.
- REQ-PROJ-007 left: telemetry is top-level only (REQ-PROJ-003), so a module inherits nothing new.
- REQ-PROJ-009 left: the default config does not turn telemetry on.
- REQ-PROJ-010 left: creating a change is unchanged; the `.gitignore` is written with the first event (new REQ in project).
- REQ-PROJ-011 left: phases are unchanged; moving records an event (new REQ in cli).
- REQ-PROJ-013 left: running commands is unchanged; `run` records an event.
- REQ-PROJ-014 left: the run cache's fingerprint already excludes `.specworks/`, so the log never stops a result being reused.
- REQ-PROJ-024 left: the log is git-ignored, so committing a phase stages it never.
- REQ-PROJ-025 modified: it points to the new REQ-PROJ-032 for the telemetry settings, which it would otherwise refuse as unknown keys.
- REQ-PROJ-029 left: docs folders are unrelated.
- REQ-FLOW-001, REQ-FLOW-002 left: `events.jsonl` is not an artifact.
- REQ-FLOW-003, REQ-FLOW-004, REQ-FLOW-006, REQ-FLOW-007, REQ-FLOW-008, REQ-FLOW-011, REQ-FLOW-014, REQ-FLOW-017 left: gates and starting a phase behave the same; the CLI records their results.
- REQ-FLOW-005 left: the specified fingerprints do not cover the log.
- REQ-FLOW-010, REQ-FLOW-016 left: review.md is read and written as before; `finding` records an event.
- REQ-FLOW-013 left: validate's verdict is unchanged; the CLI records it.
- REQ-CLI-001 left: the new command follows the same output and error rules.
- REQ-CLI-002 left: naming a change is unchanged; `status` adds telemetry IDs (new REQ).
- REQ-CLI-004 modified: `context` shows the telemetry state.
- REQ-CLI-006 left: `new`, `phase` and `abandon` behave the same; they record events (new REQ).
- REQ-CLI-007 left: close behaves the same; it records an event, sent by the commit after it.
- REQ-CLI-012 modified: commit sends the queued events and reports it.
- REQ-CLI-013 modified: `telemetry.*` is always set in the top level's config.
- REQ-CLI-016 left: spec find is unrelated.

## Impact

- Code: `core/config.py`, `core/validators.py`, `core/config_file.py` (the
  block and `config set`); a new event log module in `core`; a new Langfuse
  client in `tools`; `cli/changes.py`, `cli/workflow.py`, `cli/project.py`
  (recording events, `telemetry push`, `context`, `status`).
- Network: the first outbound HTTP in specworks (stdlib `urllib`, HTTPS to the
  configured host), only from `commit` and `telemetry push`, only when opted in
  and keys are set.
- Data: a git-ignored `events.jsonl` (and sent marker) per change, moved with
  the change to the archive.
- Dependencies: none added.

## Assumptions

- `SPECWORKS_LANGFUSE_HOST` overrides `telemetry.host`; with neither, the host is
  `https://cloud.langfuse.com`.
- The send timeout is 5 seconds per request.
- Events are recorded only for commands that name a change; a command that
  fails before resolving its change records nothing.

## Out of Scope

- Configuring Claude Code's or Copilot's own telemetry export to carry the
  trace ID (a follow-up, once Claude Code's OTel output has been checked
  against Langfuse).
- Sending any content (code, spec text, prompts, command output).
- Sending from `close` itself: the commit that follows close sends its events.
- Live streaming, or any backend other than Langfuse.
- Recording events for commands that do not act on a change (`context`,
  `list`, `spec find`, `skills`).
