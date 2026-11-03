# Design: capability-tests

## Context

See proposal.md. Today `review_tests_pass` and `tests_pass`
(`src/specworks/workflow/checks.py`) both run `commands.test` through
`command_check` → `cached_run` (`src/specworks/core/runner.py`). `cached_run`
reads the command from the config and keys its reuse on the command string plus
the tree fingerprint. A change's deltas know their capability
(`ctx.analysis.specs.deltas[*].cap`, a `CapabilityRef` with its module and,
for a registered one, its `Capability`), and `ctx.report.changed` lists the
changed files relative to the workspace root (`None` without git).

## Goals / Non-Goals

**Goals:**
- One place computes which tests the review gate runs (a plan), shared by the
  test check and the missing-folder warning.
- The scoped run reuses `cached_run`, so result reuse and `--fresh` work unchanged.

**Non-Goals:**
- No change to validate, the design gate, tag scanning or `specworks run test`.

## Decisions

### The test folder is derived, never required

`Capability.tests` (empty when not set) and `Config.tests_dir` (default `tests`)
give `Capability.tests_path(module_root, tests_dir)`; a capability new in the
change (no `Capability` yet) uses `<module root>/<tests_dir>/<name>`. Both are
validated like `docs_dir` and a capability path (`validate_relative`).
Serves: REQ-PROJ-027, REQ-PROJ-003, REQ-PROJ-004.

### Filling `{paths}` and the cache key

`scoped_command` turns the folders into paths relative to the module's folder
(POSIX separators), quotes each one (`shlex.quote`; `subprocess.list2cmdline`
on Windows, whose shell has no single quotes), joins them with spaces and
replaces every `{paths}`. `run_scoped` passes that filled command to
`cached_run` through a new keyword-only `command` argument, so the cache key is
the filled command: the same folders reuse, other folders run.
`run_command` gets the same `command` argument; without it, key `test_scoped` is
refused before anything runs (`specworks run test_scoped`).
Alternative: a separate cache for scoped runs; rejected as a second copy of the
reuse rules. Serves: REQ-PROJ-028, REQ-PROJ-013.

### The plan: touched capabilities → runs, or the full suite

`test_plan(ctx)` (cached on the context as `ctx.test_plan`) returns a `TestPlan`:
- touched = every delta's capability, plus every workspace capability whose code
  path or test folder contains a changed file (any kind, deleted included);
  nested capabilities can both be touched;
- `full=True` when nothing is touched, when a touched capability's module has no
  `test_scoped`, or when a touched test folder does not exist (`missing` lists
  those folders, relative to the workspace root);
- otherwise `runs`: one entry per module, its touched folders sorted, modules in
  workspace order.

`review_tests_pass` runs the plan: the full suite through `tests_pass` as now,
or each run through `run_scoped`, one `Check` named
`the touched capabilities' tests pass (commands.test_scoped)` whose details hold
each run's command line and, on a failure, its output tail. `--no-run` and the
`--allow-open` warning behave as for the full suite. A separate warning check,
`test_folders_exist`, reports `missing`; it returns `None` when nothing is
missing or `test_scoped` is not configured. Serves: REQ-FLOW-017, REQ-FLOW-011.

### `context` shows the test folder

`testsPath` (relative to the workspace root) next to `docsPath`. Serves: REQ-CLI-004.

### Setting `commands.test_scoped`

`set_config_value` refuses a non-empty `test_scoped` without `{paths}` before
writing, with the same message the loader gives. Serves: REQ-PROJ-025.

## Interfaces

Agreed with the user

Checked against the code: every entry extends the existing `core/config`,
`core/runner` and `workflow/checks` conventions (`Capability.tests_path` mirrors
`docs_path`; the new `command` arguments are keyword-only with a `None` default,
so no existing caller breaks; nothing is **BREAKING**). The stubs follow the
tasks: `Capability.tests_path` returns `root / self.path`, `scoped_command`
returns the unfilled command, `run_scoped` raises `NotImplementedError`,
`test_plan` returns a full-suite plan and `test_folders_exist` returns `None`,
so the existing suite stays green. `testsPath` in `context` is behaviour only
(task 4.2), with no stub. Tests reach `test_plan` and `test_folders_exist`
through the CLI or `from specworks.workflow import checks`, never by importing
those names into a test module (pytest would collect them as tests).

In the stubs, `COMMAND_KEYS` keeps its five keys: adding `test_scoped` makes the
config, `specworks run` and `config set` accept it (behaviour), and turns red the
existing tests of AC-PROJ-003.4 and AC-PROJ-013.4 that list the old keys. The code
half adds it (task 2.3), after `test`, as listed below.

- `src/specworks/core/config.py`:
  - `COMMAND_KEYS = ("test", "test_scoped", "lint", "typecheck", "build", "format")`;
    `SCOPED_TEST_KEY = "test_scoped"`, `PATHS_PLACEHOLDER = "{paths}"`,
    `DEFAULT_TESTS_DIR = "tests"` (REQ-PROJ-003, REQ-PROJ-013, REQ-PROJ-027)
  - `Capability.tests: str = ""` and `Capability.tests_path(self, root: Path, tests_dir: str) -> Path` (REQ-PROJ-004, REQ-PROJ-027)
  - `Config.tests_dir: str = DEFAULT_TESTS_DIR`; `CONFIG_KEYS` gains `tests_dir`, `CAPABILITY_KEYS` gains `tests` (REQ-PROJ-027)
- `src/specworks/core/runner.py`:
  - `scoped_command(ws: Workspace, module: Module, folders: Sequence[Path]) -> str` (REQ-PROJ-028)
  - `run_scoped(ws: Workspace, module: Module, folders: Sequence[Path], reuse: bool = True) -> RunResult` (REQ-PROJ-028)
  - `run_command(..., *, command: str | None = None)` and `cached_run(..., *, command: str | None = None)`:
    an explicit command to run under `key`; `run_command` refuses key `test_scoped` without one (REQ-PROJ-013, REQ-PROJ-028)
- `src/specworks/workflow/checks.py`:
  - `TestPlan(full: bool, runs: list[tuple[Module, list[Path]]], missing: list[str])` dataclass (REQ-FLOW-017)
  - `test_plan(ctx: GateContext) -> TestPlan` and `GateContext.test_plan` (cached property) (REQ-FLOW-017)
  - `test_folders_exist(ctx: GateContext) -> Check | None` (REQ-FLOW-017)
  - `review_tests_pass(ctx)` keeps its signature; it runs the plan (REQ-FLOW-011, REQ-FLOW-017)
- `src/specworks/workflow/gate.py`: the review gate lists `c.test_folders_exist` before `c.review_tests_pass` (REQ-FLOW-017)
- `src/specworks/cli/project.py`: `context` JSON capability entries gain `testsPath` (REQ-CLI-004)

## Diagrams

No structural change: new functions inside the existing `core/config`,
`core/runner` and `workflow/checks` components, and no new dependency between them.

## Risks / Trade-offs

- [A scoped run misses a test that breaks in another capability] -> validate
  still runs the full suite, blocking.
- [Quoting differs per shell] -> one helper, tested with a space in a folder name.
- [A change touches many capabilities] -> one run per module, never one per capability.

## Migration / Rollback

None: without `test_scoped` nothing changes. The default config written by
`init` gains commented examples of `tests_dir` and `commands.test_scoped`.

## Open Questions

None.
