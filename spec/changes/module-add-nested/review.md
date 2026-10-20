# Review: module-add-nested

Base: `origin/main`

## Findings

- [x] R1 **spec-gap** `module add` around an existing module (`module add services` after `module add services/billing`, from the top level) writes the link, after which the new loading check (AC-PROJ-006.8) refuses the workspace and every command fails until the config is fixed by hand. No criterion of REQ-CLI-005 covers a folder that holds a module (`src/specworks/cli/project.py:220`)
  - **Decision**: back to specify: add AC-CLI-005.7 to REQ-CLI-005: `module add` refuses a folder that holds a module already in the workspace, naming that module, and writes nothing. Chosen with the user over moving the inner links or accepting the load error.
  - done in specify: REQ-CLI-005 MODIFIED again: its description says `module add` refuses a folder that holds a module, and AC-CLI-005.7 was added; design decision and tasks 3.1-3.2 added

  - **Resolved**: AC-CLI-005.7 tested in `tests/test_modules.py`; `module_add` refuses a folder holding a module before writing anything (cycle 2)
- [x] R2 **code-gap** `_check_nesting` crashes with `ValueError: max() arg is an empty sequence` when no other module's folder holds a module, e.g. a module symlinked to a folder outside the workspace; REQ-PROJ-006 (`src/specworks/core/workspace.py:265`)
  - **Decision**: back to code: pass `default=None` to `max` and skip a module no other module holds (nothing can list it past its container), with a test that such a workspace gets past the check. That a module outside the workspace folder already crashes `context` on `origin/main` (`Workspace.rel`) is a separate, pre-existing bug, left out of this change.
  - **Resolved**: `_check_nesting` passes `default=None` and skips a module no other module holds; tested with a module symlinked outside the workspace, tagged AC-PROJ-006.8 (cycle 3)
- [ ] R3 **spec-gap** `init <path>` links a folder that holds a module just as `module add` did before R1 (`init services` after `module add services/billing`), and the workspace then no longer loads. REQ-CLI-003 has no criterion for it (`src/specworks/cli/project.py:50`, `link_to_parent`)
  - **Decision**: back to specify: REQ-CLI-003 MODIFIED with a new criterion: `init <path>` refuses a folder that holds a module of the parent workspace, naming it, and writes nothing; `--no-link` still creates an unlinked project. Chosen with the user over initialising without the link or tracking it separately.
  - done in specify: REQ-CLI-003 MODIFIED: its description says `init` refuses a folder that holds a module, and AC-CLI-003.6 was added; design decision (shared `held_module` helper) and tasks 4.1-4.2 added

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

`module add` now links a folder to the innermost module holding it, and loading
refuses a module listed past that module (AC-CLI-005.6, AC-PROJ-006.8). One
spec gap: adding a folder around an existing module leaves a workspace that no
longer loads; sent back to specify (R1) and fixed in cycle 2. Cycle 2 review: the
nesting check crashes on a module no other module holds (R2), back to code, fixed in cycle 3. Cycle 3 review: `init <path>` has the same gap
as R1 (R3), back to specify.
