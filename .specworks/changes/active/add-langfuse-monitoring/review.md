# Review: add-langfuse-monitoring

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **test-gap** AC-PROJ-003.10: tests/project/test_telemetry.py test_ac_proj_003_10_telemetry_in_a_module (~line 76) calls load_config on billing's folder, which only reads that file and never refuses; the refusal is in load_module_config (src/specworks/core/workspace.py:195), as designed and as for 'tools' (AC-PROJ-003.7). The test fails with DID NOT RAISE.
  - **Proposal**: back to test: load the workspace (run_json('context') or load_workspace) and assert the error names 'telemetry' and the top level, like tests/project/test_modules.py:23 for AC-PROJ-003.7
- [ ] R2 **test-gap** AC-PROJ-030.2, AC-PROJ-030.4, AC-PROJ-030.5: tests/project/test_telemetry.py sets up with opt_in then add_change, and 'new' itself records a 'new' event (REQ-CLI-017), so events.jsonl and .gitignore exist before the test acts: 030.2 finds .gitignore already there, 030.4 cannot mkdir events.jsonl (FileExistsError), 030.5 sees ['new','gate','commit'] instead of ['gate','commit']. The code is right.
  - **Proposal**: back to test: create the change before opting in (add_change, then opt_in), or remove events.jsonl and .gitignore after new, so each test starts from a change folder with no log

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

The base `origin/main` does not hold the previous change, test-folders-per-capability (closed and committed on this branch, not pushed yet), so the diff lists its test moves. Its own review covered them.

- `tests/support/langfuse.py`: test helper for this change (fake Langfuse server, `opt_in`, `event_lines`), used by the tests tagged AC-PROJ-030.*, AC-INTEG-008.*, AC-INTEG-009.*, AC-CLI-012.5-7, AC-CLI-017.*, AC-CLI-018.*
- `tests/support/archive.py`, `tests/support/capability_tests.py`, `tests/support/cli.py`, `tests/support/close_phase.py`, `tests/support/code_phase.py`, `tests/support/commit.py`, `tests/support/config_set.py`, `tests/support/design_phase.py`, `tests/support/diagrams.py`, `tests/support/find_requirements.py`, `tests/support/findings.py`, `tests/support/merge.py`, `tests/support/modules.py`, `tests/support/propose.py`, `tests/support/run_cache.py`, `tests/support/skills.py`: shared test helpers from test-folders-per-capability (outside this change's diff since b7f8118)
- `tests/test_archive.py`, `tests/test_cli.py`, `tests/test_close_phase.py`, `tests/test_code_phase.py`, `tests/test_design_phase.py`, `tests/test_diagrams.py`, `tests/test_modules.py`, `tests/test_propose.py`, `tests/test_run_cache.py`, `tests/test_skills.py`, `tests/test_test_phase.py`: untagged tests left at the top by test-folders-per-capability (skill wording, walkthrough-style checks); not part of this change
- `tests/test_capability_tests.py` (deleted): split into the capability folders by test-folders-per-capability

## Summary

<!-- Two or three lines: what was found, what changed in code, specs and design, and anything sent back to an earlier phase. -->

The code matches the specs and the design. Each listed command records its event with only its own fields, and the log is kept git-ignored. Settings and keys are read only from the `SPECWORKS_LANGFUSE_*` variables, and no key appears in any reason. Events are sent in batches of 100, with `events.sent` keeping count. Push and commit both report on sending, `status` shows the IDs, and `config set telemetry.*` works. 987 tests pass. Two test-gaps are open (R1, R2: 5 failing tests in `tests/project/test_telemetry.py`), both sent back to test. No change to code, specs or design is proposed.
