# Review: capability-tests

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **quality** REQ-PROJ-028: scoped_command resolves each test folder before making it relative to the module (src/specworks/core/runner.py:181), so a test folder that is a symlink to a folder outside the module (e.g. tests/auth -> /shared/auth) raises an uncaught ValueError; through the review gate (scoped_tests_pass, src/specworks/workflow/checks.py:371, which catches only CommandError) the gate crashes with a traceback instead of reporting a check
  - **Proposal**: back to implement: test half adds a test (tagged @ac AC-PROJ-028.1) that fills {paths} for a test folder that is a symlink to a folder outside the module and expects the folder's own relative path (tests/auth); code half makes the folder relative to the module without resolving it (folder.relative_to(module.root), both built from module.root, falling back to os.path.relpath), so the gate never raises
  - **Decision**: back to implement: the test half adds a test tagged @ac AC-PROJ-028.1 where the test folder is a symlink pointing outside the module, expecting tests/auth in the filled command; the code half makes the folder relative to the module without resolving it, so the review gate cannot crash
  - done in implement: code half: scoped_command makes each test folder relative to the module without resolving it (_relative_to_module in src/specworks/core/runner.py: Path.relative_to(module.root), falling back to os.path.relpath), so a symlinked test folder keeps its path (tests/auth) and the review gate cannot raise ValueError
  - confirmed in review: confirmed in review cycle 2: scoped_command makes each folder relative to module.root without resolving it (_relative_to_module, src/specworks/core/runner.py), the review gate passes unresolved folders built from module.root (src/specworks/workflow/checks.py:325,329), and test_ac_proj_028_1_a_test_folder_that_links_outside_the_module_keeps_its_own_path (tagged @ac AC-PROJ-028.1) expects tests/auth for a symlink outside the module; the suite passes (931 tests)

## Changed files without tags

None: `specworks review` lists no untraced source or test file and no deleted file.

## Summary

Cycle 1: the full suite passed (930 tests) and every requirement and criterion of the change was tagged;
the code matches design.md's Interfaces and Decisions (plus internal helpers `check_scoped_command` and
`scoped_tests_pass`). One quality finding (R1, a symlinked test folder crashes the scoped command) went back
to implement. Cycle 2: R1 is carried out by both halves (a symlink test for AC-PROJ-028.1, and
`_relative_to_module` in runner.py, an internal helper) and closed; `specworks review` lists no new drift and
the suite passes (931 tests). No open finding, no spec or design change, nothing accepted. Candidate for a later change: the review and build
skills' text could say that the review gate runs only the touched capabilities' tests when
`commands.test_scoped` is set.
The gate's warning that REQ-FLOW-011's tests did not change needs no finding: its one changed behaviour (the
scoped run, also under `--allow-open`) is checked by the AC-FLOW-017 tests in `tests/test_capability_tests.py`
(AC-FLOW-017.6 for the warning), and AC-FLOW-011.7's tests still cover the full-suite path.
