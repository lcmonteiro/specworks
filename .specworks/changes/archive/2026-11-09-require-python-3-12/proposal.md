# Proposal: require-python-3-12

## Why

The `harness` extra needs Python 3.12+, but the project still supports 3.11, which keeps environment markers, a harness-less 3.11 CI job, a dead version check and a 3.11 default venv. Making 3.12 the minimum removes them (see refinement.md, Option A).

## What Changes

- **BREAKING**: `requires-python` goes from `>=3.11` to `>=3.12`; pip and uv refuse to install specworks on 3.11.
- `.python-version`, ruff `target-version` and mypy `python_version` become 3.12.
- The `; python_version >= '3.12'` markers on the harness extra and the dev group go, and `uv.lock` is regenerated.
- CI drops the 3.11 job and its harness-less coverage step; every job tests and covers the harness.
- `specworks harness` drops its `sys.version_info` check; its missing-extra error no longer names a Python version.
- The docs and the project context say "Python 3.12+".

## Capabilities

### Modified Capabilities

- `cli`: REQ-CLI-022 (harness): the missing-extra failure says to install `specworks[harness]` without naming a Python version.

## Related requirements

- REQ-CLI-022 modified
- REQ-HARNESS-001 left: describes the chat, not the Python version
- REQ-SPECS-015 left: "works on Python 3.11" is only sample task text in a scenario, not a statement about the supported versions

## Impact

- Code: `src/specworks/cli/harness.py` (the check and `EXTRA_MISSING`), `tests/cli/test_harness.py`.
- Packaging and tooling: `pyproject.toml`, `uv.lock`, `.python-version`, `.github/workflows/ci.yml`, `.specworks/config.yml` context.
- Docs: `CLAUDE.md`, `docs/architecture.md`, the `cli` and `harness` living docs (written at close), and docstrings in `src/specworks/harness/__init__.py` and `tests/harness/conftest.py`.
- Users on Python 3.11 can no longer install the next release.

## Out of Scope

- Refinement outcomes 1 to 4 (3.11 installs refused, a 3.12+ default venv, harness tested and covered on every CI job, docs saying 3.12+) are packaging, CI and docs: they have no requirement, and are checked by `uv lock`, the CI run and review.
- Rewriting code to 3.12-only idioms (Option C), dependency upgrades, and any change to the harness behaviour.
