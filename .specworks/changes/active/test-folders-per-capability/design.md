# Design: test-folders-per-capability

## Context

See `proposal.md`. Tags are comments right above a test (`# @ac AC-...`),
before its decorators. Tests import `helpers` and `samples` flat; files
define their own `runner`, `run_json`, `REF`, `project` and so on, so these
names repeat across files with different values.

## Goals / Non-Goals

**Goals:**
- One folder per capability holding exactly the tests tagged for it.
- Same tests, same results; no helper code duplicated.

**Non-Goals:**
- Changing any test's body, name or tags; any change in `src/`.

## Decisions

### Split by the first tag's capability

A test goes to the folder of the capability of its first `@ac` tag. Each
file keeps its name in every folder it splits into (`tests/cli/test_commit.py`,
`tests/project/test_commit.py`), with its docstring and the imports it uses.
The 11 tests tagging two capabilities stay whole in their first one's folder.
Alternative: copy them into both folders; rejected, the full suite would run
them twice.

### Shared helpers in `tests/support/<topic>.py`

A helper, constant or fixture used (directly or through another helper) by
the tests of more than one part moves to `tests/support/<topic>.py`, one
module per original file, imported by name. Names repeat across files with
different values, so one shared module for all would clash. A shared fixture
becomes a plain `make_<name>` function in the support module, and each part
keeps a fixture of the same name and decorator that returns it; importing
fixtures instead would trip ruff's unused-import and redefinition rules.
An autouse fixture goes to every part of its file.

### importlib import mode

With file names repeated across folders that are not packages, pytest's
default import mode refuses the second `test_commit.py`. `pyproject.toml`
sets `addopts = "--import-mode=importlib"` and `pythonpath = ["tests"]`,
which keeps `from helpers import ...` and makes `from support.<topic>
import ...` work, with no `__init__.py`.

### Scoped command

`commands.test_scoped: uv run pytest {paths}`; `tests_dir` stays at its
default `tests`, so no capability needs a `tests:` override.

## Interfaces

None: no API change.

## Diagrams

No structural change.

## Risks / Trade-offs

- [a test tagged for two capabilities runs only with its first one's folder]
  -> validate runs the full suite.
- [a test depending on another capability's code breaks unseen in review]
  -> validate runs the full suite, blocking.

## Open Questions

None.
