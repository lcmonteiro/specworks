# Refinement: code-half-no-tests

## Problem

The code half of implement runs the whole test suite several times: after
each `[code]` task, in its own checks, and in `gate code`. The change's new
`@ac` tests are written by the test half in parallel, so in the code half
they are missing or red by design, and the tests only meet the code in
review anyway. Running the suite in the code half costs time and blurs the
split between the halves; the code half only needs to know that the code
compiles and is clean.

## Outcomes

- Running `/specworks-code` never runs the project's test command, neither
  after a task nor in its checks.
- `specworks gate code` runs `build`, `typecheck` and `lint`, each only when
  it is configured, and never `commands.test`; a failing one blocks the gate.
- With none of `build`, `typecheck` or `lint` configured, `gate code` passes
  with a warning: no build, typecheck or lint command configured, the tests
  run in review.
- The tests, existing and new, first run in review: `gate implement` (and so
  `start review`) no longer runs the suite; `gate review` still does.

## Context

**Observed:**
- `src/specworks/workflow/gate.py`: `GATE_CHECKS["code"]` ends with
  `c.code_tests_pass`; `GATE_CHECKS["test"]` runs no command; `gate implement`
  is the test gate then the code gate. `GATE_CHECKS["design"]` has
  `stubs_build("build")`, `stubs_build("typecheck")` (each only when
  configured) and `existing_tests_pass`.
- `src/specworks/workflow/checks.py`: `code_tests_pass` runs `commands.test`,
  a warning instead of blocking while the change has tests of its own;
  `review_tests_pass` runs the suite for `gate review`.
- Living spec `workflow` (`src/specworks/workflow/docs/spec.md`):
  REQ-FLOW-008 Gate code requires "a configured test command whose run
  passes" (AC-FLOW-008.1, .3, .4, .7, .8 are about the tests).
  REQ-FLOW-011 Gate review runs the suite.
- `src/specworks/skills/specworks-code/SKILL.md`: step 3.6 runs
  `specworks run test` after each task; step 4 runs test, lint and
  typecheck; step 5 says the code gate runs `commands.test`.
- `src/specworks/skills/specworks-build/SKILL.md`: the suite meets the two
  halves in `gate implement` after the merge.
- REQ-SPECS-015 already warns when a `[code]` task requires the suite, and
  the tasks instruction says a `[code]` task is verified by lint, typecheck
  or observable behaviour: consistent with this change.
- Here `commands.typecheck` is `uv run mypy` and `commands.lint` is ruff.

**Assumed:**
- No user relies on `gate code` to catch a broken existing test before
  review; review's gate and validate still catch it.

## Constraints

- [hard] `gate review` and `validate` keep running the full suite.
- [hard] The design gate and the test half are unchanged.
- [soft] Reuse the design gate's command checks rather than add new ones.
- [soft] The code skill stops reading or running this change's tests, as
  it already does for reading them.

## Options

### Option A: compile checks in the code gate

Replace `code_tests_pass` in `GATE_CHECKS["code"]` with checks for
`build`, `typecheck` and `lint` (each only when configured, as
`stubs_build` does), plus one warning when none is configured. Update the
code skill (no `run test`; its checks are build, typecheck and lint) and
the build skill (the suite meets the halves in review).

- **Pros:** meets every outcome; small, reuses existing checks; one rule.
- **Cons:** a broken existing test is only seen in review.
- **Effort:** S
- **Touches:** workflow (REQ-FLOW-008 modified), skills text
- **Outcomes:** meets all four.

### Option B: A, behind a config switch

As A, plus a top-level key (e.g. `code_runs_tests`, default `false`) that
puts the tests back in the code gate.

- **Pros:** a way back for projects that want the tests early.
- **Cons:** a config key, `config set`, docs and tests nobody asked for.
- **Effort:** M
- **Touches:** workflow, project (config), cli (`config set`), skills text
- **Outcomes:** meets all four.

### Option C: skill text only

The code skill stops running the tests; `gate code` keeps running them.

- **Pros:** smallest.
- **Cons:** the gate still runs the suite, so `start review` does too.
- **Effort:** S
- **Touches:** skills text
- **Outcomes:** meets the first; fails the other three.

## Recommendation

Option A, with `lint` added to the code gate next to `build` and
`typecheck`: it meets every outcome with the smallest change, and keeps the
tests where the halves meet, in review.

## Open Questions

- None.

## Candidate Capabilities

- `workflow`: modified - the code gate's checks (REQ-FLOW-008), and
  `gate implement` no longer running the suite.
- The skill text (`specworks-code`, `specworks-build`) has no capability.
