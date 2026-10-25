# Proposal: baseline-project

## Why

Record the existing behaviour of `project` (the project model in
`src/specworks/core`), so later changes can MODIFY its requirements instead of
only ADDING them.

## What Changes

- No behaviour change. The behaviour `project` already has is written down as
  requirements, and the existing tests and code are tagged with `@ac` / `@req`.
- One new test covers a criterion that no test checks yet: a module inherits
  the top-level commands it does not set itself.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: its first requirements (REQ-PROJ-001..015): finding and reading the
  config, validating it, capabilities and ID prefixes, the workspace of modules
  and what they inherit, editing the config, the default config, changes and
  their phases, archived changes, running the project's commands and reusing
  their results, and reading project files.

## Impact

Comment tags in `src/specworks/core/*.py` and in the tests that check these
behaviours (`tests/test_cli.py`, `test_modules.py`, `test_run_cache.py`,
`test_archive.py`, `test_close_phase.py`, `test_code_phase.py`,
`test_diagrams.py`, `test_propose.py`); one new test. No API, data or
dependency change.

Behaviour that lives in the CLI layer (resolving a change reference across
modules, `--fresh`, refusing a prefix already in use on `capability add`,
creating `<dir>/changes/archive/` on `init`) is left to the `cli` baseline.

## Out of Scope

Suspected bugs and unclear behaviour found while reading the code. Each one is a
candidate for its own change (`/specworks-refine`):

- **Two capabilities may share one code path.** Neither loading the config nor
  `capability add` checks it, so both would write their living docs to the same
  `<path>/<docs_dir>/` and overwrite each other at close.
- **The config marker is documented as "the first line" but is matched on any
  line.** `config.py` says the first line `specworks: 1` marks the file, but any
  line `specworks: <n>` does.
- **Run reuse can crash on an unreadable untracked file.** If an untracked file
  can't be read (no permission), or on POSIX its name isn't UTF-8, the run
  fingerprint raises a raw `OSError` / `UnicodeDecodeError` instead of falling
  back to a real run.
- **A module path that leads back to an ancestor (through a symlink) is not
  detected.** Loading the workspace would recurse without end.
