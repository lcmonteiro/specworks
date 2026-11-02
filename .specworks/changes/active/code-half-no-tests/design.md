# Design: code-half-no-tests

## Context

`GATE_CHECKS["code"]` in `src/specworks/workflow/gate.py` ends with
`c.code_tests_pass`, which runs `commands.test` and turns a red suite into a
warning once the change has tests of its own (`own_tests`). The design gate
already runs `build` and `typecheck` only when configured, through
`stubs_build(key)` in `gate.py`, and validate runs `lint` and `typecheck`
through `optional_command` in `checks.py`. See proposal.md for why the code
gate stops running the tests.

## Goals / Non-Goals

**Goals:**
- The code gate runs build, typecheck and lint when configured, never the
  test command (REQ-FLOW-008).
- One warning when none of the three is configured.
- The code and build skills match the gate.

**Non-Goals:**
- Changing the design gate, the test gate, the review gate or validate.
- Changing how commands run or reuse cached results (`command_check`,
  `cached_run`).

## Decisions

### One check per configured command

The code gate gets one check per command, `build`, `typecheck` and `lint` in
that order, each skipped (`None`) when the command is not configured, as
`stubs_build` does for the design gate. A separate check gives the warning
when none of them is configured. Alternatives: one combined check running
all three (one failure hides the others' output), or `optional_command`,
which shows an "ok, not configured" line for each missing command (noise, and
AC-FLOW-008.10 wants no line for them). Serves: REQ-FLOW-008.

### `code_tests_pass` goes; `own_tests` stays

`code_tests_pass` has no other caller and is removed. `own_tests` and
`not_blocking` stay: the design gate's `existing_tests_pass` and the review
gate still use them. Serves: REQ-FLOW-008.

### The suite warning of `check` points at review

The REQ-SPECS-015 warning for a `[code]` task that requires the suite says
the suite runs in review after the merge instead of in `gate implement`. Its
requirement ("the suite runs after the merge") stays true; only the message
changes.

### Skills

- `specworks-code`: step 3.6 runs the task's own checks only (no
  `specworks run test`); step 4 runs build, typecheck and lint; step 5
  describes the gate as build, typecheck and lint, the tests meeting the
  code in review.
- `specworks-build`: the halves' tests meet the code in review, not in
  `gate implement`.

### Pinned wording

- Code gate check names: `the code builds (commands.build)`,
  `typecheck passes (commands.typecheck)`, `lint passes (commands.lint)`.
- The warning check is named `build, typecheck and lint` with the detail
  `no build, typecheck or lint command configured: the tests run in review`.
- The REQ-SPECS-015 suite warning:
  `task {num} [code] requires the suite (specworks run test): the suite runs in review after the merge; `
  followed by the existing `verify it with lint, typecheck or observable behaviour`.

## Interfaces

- `src/specworks/workflow/checks.py`: `code_command(key: str, name: str) -> CheckFn`
  (a check that runs `commands.<key>`, or `None` when it is not configured)
  and `no_code_commands(ctx: GateContext) -> Check | None` (the warning
  when none of build, typecheck and lint is configured, else `None`)
  (REQ-FLOW-008). `code_tests_pass` is removed.
- `src/specworks/workflow/gate.py`: `GATE_CHECKS["code"]` lists
  `code_command("build", ...)`, `code_command("typecheck", ...)`,
  `code_command("lint", ...)` and `no_code_commands` in place of
  `code_tests_pass` (REQ-FLOW-008).

## Diagrams

No structural change.

## Risks / Trade-offs

- [a broken existing test is no longer caught before review] -> `gate review`
  and validate still run the full suite and block on it.
- [lint now blocks the code gate in projects with a strict linter] -> it runs
  only when `commands.lint` is configured, and the code skill already runs
  lint in its checks.
