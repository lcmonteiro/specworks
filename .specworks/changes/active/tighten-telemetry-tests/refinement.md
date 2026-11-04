# Refinement: tighten-telemetry-tests

## Problem

Validating `add-langfuse-monitoring` passed with two correctness warnings: two
acceptance tests check less than their criteria say. A test that accepts a 9 s
timeout, or never builds the module-qualified session ID, lets those behaviours
regress unnoticed. Now is the time because the feature was just closed and the
gaps are cheap to fix while its context is fresh.

## Outcomes

- Validating the telemetry capabilities reports no warning for AC-INTEG-009.3 and AC-PROJ-031.2.
- A timeout regression in sending events (6 s or more) fails a test.
- A change in a module shows its module-qualified session ID (`billing:cleanup`) in `status`, and a test fails if that is built wrongly.
- No behaviour of the CLI changes.

## Context

**Observed:**
- `TIMEOUT = 5.0` in `src/specworks/tools/langfuse.py`. AC-INTEG-009.3 (`tests/integrations/test_langfuse.py`) says "about 5 seconds" but asserts `elapsed < 10`.
- AC-PROJ-031.2 (`tests/project/test_telemetry.py`) calls `session_id("billing:cleanup")` with the ref already built. The qualifying (`module.qualify(change.name)`) happens in `src/specworks/cli/telemetry.py` (`telemetry_ids` for `status`, `_send` for sending), and no test covers it for a module change. The only CLI check (`tests/cli/test_telemetry.py`, session ID `add-login`) is top-level.
- Capabilities touched: `integrations` (REQ-INTEG-009) and `cli` (REQ-CLI-019, `status` shows the IDs); `project` REQ-PROJ-031 is unchanged.

**Assumed:**
- A 7 s bound is loose enough for slow CI and tight enough to catch a regression.
- A module workspace helper in `tests/support` can build a `billing` change for the `status` test.

## Constraints

- [hard] No source behaviour change; tests and spec text only.
- [hard] Tests carry `@ac` tags, and IDs are never renumbered or reused.
- [soft] Keep the timeout test fast and not flaky on Windows and macOS CI.

## Options

### Option A: Reword the timeout criterion and add a CLI scenario

AC-INTEG-009.3 says "within 7 seconds" and the test asserts `elapsed < 7`. A new
scenario under REQ-CLI-019 checks `status` on a change in module `billing`: its
`sessionId` is `billing:cleanup` and its `traceId` differs from a top-level `cleanup`.

- **Pros:** the criteria and tests agree; the qualified path is covered where it lives.
- **Cons:** touches two specs.
- **Effort:** S
- **Touches:** `integrations`, `cli`
- **Outcomes:** meets all.

### Option B: Test only

Keep the criteria, tighten the assertion to `4.5 <= elapsed < 6`, and add the CLI test without a new scenario.

- **Pros:** no spec change.
- **Cons:** timing window is more flaky; the new test has no criterion, so it breaks the trace.
- **Effort:** S
- **Touches:** none
- **Outcomes:** meets the timeout outcome weakly; fails the session ID outcome.

## Recommendation

Option A, as agreed with the user (timeout "within 7 seconds"; `status` scenario
for a module change). Not covered: the sending path's session ID, and the old
REQ-PROJ-025 long-description warning, which stays accepted.

## Open Questions

- None.

## Candidate Capabilities

- `integrations`: modified - AC-INTEG-009.3 wording and test bound.
- `cli`: modified - new scenario under REQ-CLI-019 for a module change's IDs.
