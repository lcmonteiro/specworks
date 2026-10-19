# Proposal: baseline-cli

## Why

Record the existing behaviour of `cli` (`src/specworks/cli`): the command
surface's conventions (`--json`, errors, no project), resolving a change
reference, and what the commands add on top of the capabilities they call
(`init`, the overview commands, `module add` and `capability add`, moving and
dropping changes, `close`, `diagrams`). Later changes can then MODIFY these
requirements instead of only ADDING them.

## What Changes

- No behaviour change. The behaviour `cli` already has is written down as
  requirements, and the existing tests and code are tagged with `@ac` / `@req`.
- Two new tests cover criteria that no test checks yet: `module add` refuses a
  folder outside the project, and `diagrams --dir` refuses a folder outside the
  workspace.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: its first requirements, REQ-CLI-001 to REQ-CLI-008.

## Impact

Comment tags in `src/specworks/cli/*.py` and in the tests that check these
behaviours (`tests/test_cli.py`, `test_modules.py`, `test_archive.py`,
`test_close_phase.py`, `test_diagrams.py`, `test_propose.py`,
`test_skills.py`), plus two new tests. No API, data or dependency change.

Behaviour the commands only pass through stays with its owners:
- config, changes, phases and running commands with `project`;
- gates, review, cycles and validate with `workflow`;
- rendering and skills with `integrations`;
- tasks, check, trace and the merge done by close with `specs` (not baselined
  yet).

## Out of Scope

Suspected bugs and unclear behaviour, each a candidate for its own change:

- **`module add` can link a folder that another module already owns.** It
  links the folder to the current module whenever the folder is inside it. A
  folder inside a child module (`services/billing/sub` run from the top level)
  becomes a top-level module, not a module of `billing`.
- **`run` with a key that is not a command key gives a misleading message.**
  `specworks run deploy` says `no 'deploy' command configured … add it under
  commands:`, but `deploy` isn't an allowed key, so adding it would fail.
- **`diagrams --dir` reads the folder relative to the working directory.** The
  other paths the CLI prints are relative to the workspace root; inside a
  module, `--dir src/auth/docs` means a different folder than the one printed
  back. It may be intended, but it's undocumented.
