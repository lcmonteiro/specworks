# Proposal: capability-tests

## Why

The review gate runs the whole test suite on every build cycle, even when a
change touches one capability, and tests are not grouped by capability. Giving
each capability its own test folder lets review run only what the change
touched, while validate keeps running everything.

## What Changes

- A module-level `tests_dir` setting (default `tests`) gives each capability a
  test folder `<tests_dir>/<capability>/`, relative to its module's folder; an
  optional `tests:` on a capability overrides it. Both must be relative folders
  inside the project.
- A new optional command key `test_scoped`, holding a `{paths}` placeholder
  (e.g. `uv run pytest {paths}`); a `test_scoped` without `{paths}` is refused
  when the config loads. `config set commands.test_scoped` accepts it like the
  other command keys; `specworks run test_scoped` is refused, since only the
  review gate knows the folders to fill in.
- The review gate runs `test_scoped` with the test folders of the capabilities
  the change touched (a delta spec, or a changed file under the capability's
  code path or test folder), and names them. It falls back to the full suite
  (`commands.test`) when `test_scoped` is not configured (as today), when the
  change touches no capability, or, with a warning naming the folder, when a
  touched capability has no test folder.
- `specworks context` shows each capability's test folder (`testsPath`).
- Validate is unchanged: it runs `commands.test`, the full suite.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: a capability's test folder (new), the scoped test command and how
  `{paths}` is filled (new); REQ-PROJ-003, REQ-PROJ-004, REQ-PROJ-013 and
  REQ-PROJ-025 take the new keys.
- `workflow`: the review gate's scoped test run (new); REQ-FLOW-011 points its
  "passing test suite" at it.
- `cli`: REQ-CLI-004, `context` shows each capability's test folder.

## Related requirements

- REQ-PROJ-003 modified: `tests_dir` and a capability's `tests:` are paths that
  must stay inside the project; `test_scoped` is a command key and needs
  `{paths}`.
- REQ-PROJ-004 modified: a capability mapping takes an optional `tests`.
- REQ-PROJ-013 modified: `test_scoped` is a command key; `run test_scoped` is refused.
- REQ-PROJ-025 modified: `commands.test_scoped` is settable.
- REQ-PROJ-016 left: unique docs folders; test folders may be shared or nested
  (a shared folder only runs the same tests twice over).
- REQ-SPECS-011 left: tag scanning still uses `test_globs`; a capability's test
  folder only scopes which tests the review gate runs.
- REQ-FLOW-006 left: the design gate keeps running the existing full suite with the stubs.
- REQ-FLOW-010 left: reading review.md; only matched on "review".
- REQ-FLOW-011 modified: its passing test suite is the scoped run of REQ-FLOW-017.
- REQ-FLOW-016 left: writing findings; only matched on "review".
- REQ-CLI-013 left: `config set` delegates the key list to REQ-PROJ-025.
- REQ-CLI-004 modified: `context` shows each capability's test folder.

## Impact

- `src/specworks/core/config.py` (keys, capability `tests`, `tests_dir`,
  checks), `config_file.py` (settable keys), `runner.py` (filling `{paths}`,
  refusing `run test_scoped`).
- `src/specworks/workflow/checks.py` (the review gate's test check), and the
  touched-capability computation from the change's deltas and changed files.
- `src/specworks/cli/project.py` (`context`).
- The default config template gains commented `tests_dir` and `test_scoped`
  examples. The skills' text about the review gate may mention the scoped run.

## Out of Scope

- Moving this repo's tests into per-capability folders (a later change).
- Project/module docs: architecture, capability interactions, why/what (the
  `project-docs` change).
- Running one capability's tests by hand (`specworks run test_scoped --capability ...`).
- Changing validate, the design gate, or tag scanning (`test_globs`).
