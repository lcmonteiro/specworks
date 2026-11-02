# Refinement: capability-tests

## Problem

The review gate runs the whole test suite on every build cycle, even when a
change touches one capability, so the slowest gate repeats at full cost each
cycle. Tests are not grouped by capability either: nobody can see or run one
capability's tests. This is the first of two changes; project/module-level
docs (architecture, how capabilities interact, each one's why and what) follow
as `project-docs`.

## Outcomes

- Each capability's tests live in their own folder (by default
  `tests/<capability>/`), and `specworks context` shows that folder per
  capability. Files directly in the tests folder, outside every capability
  folder, are the integration tests.
- The review gate runs only the tests of the capabilities the change touched
  (a delta spec, or changed files under the capability's code path), and its
  output names the folders it ran.
- Validate still runs the full suite (integration tests included), blocking as
  today.
- When a touched capability has no test folder yet, review runs the full suite
  and warns, naming the missing folder: review never checks less than today.
- A project that has not adopted the layout, or has no scoped test command,
  sees no change: review runs the full suite.

## Context

**Observed:**
- `review_tests_pass` and `tests_pass` in `src/specworks/workflow/checks.py`
  both run `commands.test` through `command_check` / `cached_run`
  (`src/specworks/core/runner.py`); review and validate run the same full suite.
- Command keys are a fixed list (`COMMAND_KEYS`, refused otherwise by the config
  in `src/specworks/core/config.py`); a module's commands override the top
  level's key by key.
- Capabilities have `path`, `description`, `prefix`; `docs_dir` is a module-level
  key giving `<path>/<docs_dir>/`. There is no test location per capability: tests
  link to capabilities only through `@ac` tags.
- `specworks review` already reports the change's changed files with their kind
  (`ctx.report.changed`), and a change's deltas name their capabilities.
- This repo keeps 25 test files flat in `tests/`.

**Assumed:**
- Runners in other languages accept test paths as arguments (`pytest <dirs>`,
  `go test <pkgs>`, `jest <dirs>`), so a `{paths}` placeholder is enough.

## Constraints

- [hard] Language-agnostic: no assumption about the test runner.
- [hard] Backward compatible: without the new settings, behaviour is unchanged.
- [hard] Validate keeps running the whole suite as its blocking check.
- [soft] Reuse the run cache for scoped runs, keyed so a scoped result is never
  reused for a different set of folders or for the full suite.
- [soft] Moving this repo's tests into per-capability folders is a separate,
  later change, not part of this one.

## Options

### Option A: scoped command + overridable test folder convention

A new optional command key `test_scoped` with a `{paths}` placeholder
(e.g. `uv run pytest {paths}`); a module-level `tests_dir: tests` (next to
`docs_dir`) makes a capability's folder `<tests_dir>/<capability>/`, overridden
by an optional `tests:` on the capability. Review fills `{paths}` with the
touched capabilities' folders; validate runs `commands.test`.

- **Pros:** works with any runner; `commands.test` untouched; matches the
  requested tree yet allows other layouts (e.g. Go tests next to the code).
- **Cons:** one more command key and config key to explain.
- **Effort:** M
- **Touches:** project, workflow, cli
- **Outcomes:** meets all.

### Option B: `{paths}` inside `commands.test`

One key; validate fills it with the whole tests folder.

- **Pros:** nothing new to configure.
- **Cons:** breaks runners that take no paths (`npm test`, `make test`);
  validate's "full suite" becomes "every folder", which can miss tests elsewhere.
- **Effort:** S
- **Touches:** project, workflow
- **Outcomes:** fails "no change without adoption" for such runners.

### Option C: append the paths to `commands.test`, explicit `tests:` per capability

- **Pros:** no new command key.
- **Cons:** silently breaks wrapper scripts and `npm`/`make` runners; every
  capability needs a `tests:` entry.
- **Effort:** S
- **Touches:** project, workflow
- **Outcomes:** fails backward compatibility for many runners.

## Recommendation

Option A, agreed with the user: `test_scoped` with `{paths}`, `tests_dir` with a
per-capability `tests:` override, and a full-suite fallback with a warning when a
touched capability has no test folder.

## Open Questions

- A touched capability in another module: run its tests from that module's
  folder with that module's `test_scoped`? Default assumed: yes. (who can answer:
  user, in specify)
- How the run cache keys a scoped run (by its folders). (who can answer: design)

## Candidate Capabilities

- `project`: modified - `tests_dir`, a capability's `tests:`, the `test_scoped`
  command and filling `{paths}`.
- `workflow`: modified - the review gate's scoped test run and its fallback;
  validate unchanged.
- `cli`: modified - `specworks context` shows each capability's test folder.
