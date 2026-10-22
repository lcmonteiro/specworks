# Review: git-workflow

Base: `origin/main`

## Findings

- [ ] R1 **test-gap** Seven existing tests run `init` in a folder that is not a git repository, so `init` now refuses them (AC-CLI-003.7); task 3.1 left them without `init_repo` (`tests/test_diagrams.py:270`, `tests/test_diagrams.py:279`, `tests/test_modules.py:206` x4 parametrized, `tests/test_modules.py:421`)
  - **Proposal**: back to test: call `init_repo(tmp_path)` (and in the `with_config` case of `test_a_module_outside_the_workspace_is_refused`, on the `outside` folder) before `init` in each; behaviour under test is unchanged
- [ ] R2 **test-gap** `test_init_outside_a_git_repository_is_refused_as_json` passes `--json` to `init`, which has no such option, so it fails on usage and can never pass; AC-CLI-003.7 is already checked by `test_init_outside_a_git_repository_is_refused_and_writes_nothing` (`tests/test_cli.py:95`)
  - **Proposal**: back to test: delete this redundant test
- [ ] R3 **test-gap** `test_a_module_change_branch_has_the_module_path` runs `module add services/billing`, which names the module `billing` (the folder name), so the branch is `billing/add-invoices`, not `services/billing/add-invoices`; the code follows REQ-PROJ-018 (module name, `<parent>/<child>/<name>` when nested) (`tests/test_cli.py:120`, AC-CLI-006.6)
  - **Proposal**: back to test: build a nested module (`module add tax` from inside `services/billing`) and expect `billing/tax/add-invoices`; keep the top-level module case expecting `billing/add-invoices`
- [ ] R4 **spec-gap** AC-PROJ-018.2 gives `services/billing` as the name of a nested module and `services/billing/add-login` as its branch, but a module's name is `<parent>/<child>` (`billing/tax`), and `services/billing` is its folder; the requirement text (`<parent>/<child>/<name>`) and the code are right, the example is not (`spec/changes/git-workflow/specs/project/spec.md`, AC-PROJ-018.2; `tests/test_git.py` tags AC-PROJ-018.2)
  - **Proposal**: back to specify: MODIFIED REQ-PROJ-018: AC-PROJ-018.2 says "nested module `billing/tax`" and `billing/tax/add-login`; `tests/test_git.py`'s AC-PROJ-018.2 test follows

## Changed files without tags

- `tests/helpers.py`: shared helpers (`init_repo`, `remove_repo`, `git`) for the sample projects (task 3.1); no criterion of its own
- `tests/test_walkthrough.py`: sample project now runs `init_repo` and `new --no-branch` (task 3.1); the test keeps its existing tags' meaning

## Summary

The code matches REQ-PROJ-017/018/019 and REQ-CLI-003/006 and the Interfaces in design.md; every requirement has code and every criterion a test. The suite has 9 failing tests, all test-side: unfinished `init_repo` setup (R1), a test using an option `init` lacks (R2) and a wrong module name in one test (R3), plus one imprecise criterion example (R4). Nothing was fixed here; R1 to R3 go back to test, R4 to specify. Unrelated and left out of the commit: untracked `.vscode/`.
