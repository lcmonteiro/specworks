# Review: absolute-imports

Base: `origin/main`

## Findings

- [ ] R1 **design-gap** design.md Decision 'Lazy imports stay lazy' says both indented imports are inside functions and keep `import specworks` working without the harness extra; only `src/specworks/cli/harness.py:24` is a function-level lazy import. `src/specworks/harness/workspaces.py:26` (`from specworks.harness.backend import GitBackend`) sits under `if TYPE_CHECKING:` at module level, in a module that is itself harness-only (design.md Decisions; tasks.md 2.2 repeats it). The code is right: both stay where they were.
  - **Proposal**: back to design only: in design.md's Decision, say that `cli/harness.py`'s `from specworks.harness import run_harness` stays inside `harness()` (the lazy import architecture.md requires), and that `harness/workspaces.py`'s `GitBackend` import stays under `if TYPE_CHECKING:` (type-only, not run at import time); no code or test change
  - **Decision**: back to design only: reword the Decision 'Lazy imports stay lazy': cli/harness.py's run_harness import stays inside harness(); harness/workspaces.py's GitBackend import stays under if TYPE_CHECKING:, so it never runs at import time. No code or test change.

## Changed files without tags

Import lines only (no behaviour change, `skip-specs`); none of these files had
an `@req` tag before the change, and none needs one now:

- `src/specworks/harness/__init__.py`: import rewrite only
- `src/specworks/harness/peers/adopt.py`: import rewrite only
- `src/specworks/harness/peers/baseline.py`: import rewrite only
- `src/specworks/harness/peers/close.py`: import rewrite only
- `src/specworks/harness/peers/code.py`: import rewrite only
- `src/specworks/harness/peers/design.py`: import rewrite only
- `src/specworks/harness/peers/done.py`: import rewrite only
- `src/specworks/harness/peers/onboard.py`: import rewrite only
- `src/specworks/harness/peers/refine.py`: import rewrite only
- `src/specworks/harness/peers/reopen.py`: import rewrite only
- `src/specworks/harness/peers/review.py`: import rewrite only
- `src/specworks/harness/peers/specify.py`: import rewrite only
- `src/specworks/harness/peers/start.py`: import rewrite only
- `src/specworks/harness/peers/validate.py`: import rewrite only

## Summary

The diff changes only import lines (every source file has as many lines added
as removed) and `pyproject.toml`'s ruff config. No relative import is left in
`src`, the command modules in `cli/__init__.py` keep their `--help` order
under `# isort: off`, the lazy `specworks.harness` import in
`cli/harness.py` stays inside its function, and the full suite passes (1135
tests). One design-gap: design.md misdescribes the second "lazy" import
(R1), sent back to design only. No spec, API or code change.
