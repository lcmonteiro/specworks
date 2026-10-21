# Tasks: baseline-specs

## 1. REQ-SPECS-004 Reading spec files

- [x] 1.1 Tag the tests that check the criteria of REQ-SPECS-004 with `@ac`; verify `specworks trace` lists a test for each
- [x] 1.2 Tag the code that implements REQ-SPECS-004 with `@req` in specfile.py (`parse_spec`, `living_problems`, ID helpers); verify `specworks trace` lists its code and the suite still passes

## 2. REQ-SPECS-005 Format of a delta spec

- [x] 2.1 Tag the tests that check the criteria of REQ-SPECS-005 with `@ac`; verify `specworks trace` lists a test for each
- [x] 2.2 Tag the code that implements REQ-SPECS-005 with `@req` in check.py (`_check_delta`); verify `specworks trace` lists its code and the suite still passes

## 3. REQ-SPECS-006 A delta against its living spec

- [x] 3.1 Tag the tests that check the criteria of REQ-SPECS-006 with `@ac`; verify `specworks trace` lists a test for each
- [x] 3.2 Tag the code that implements REQ-SPECS-006 with `@req` in check.py (`_check_delta`); verify `specworks trace` lists its code and the suite still passes

## 4. REQ-SPECS-007 Two active changes on one requirement

- [x] 4.1 Tag the tests that check the criteria of REQ-SPECS-007 with `@ac`; verify `specworks trace` lists a test for each
- [x] 4.2 Tag the code that implements REQ-SPECS-007 with `@req` in check.py (`_other_changes`); verify `specworks trace` lists its code and the suite still passes

## 5. REQ-SPECS-008 The proposal and the delta specs

- [x] 5.1 Tag the tests that check the criteria of REQ-SPECS-008 with `@ac`; verify `specworks trace` lists a test for each
- [x] 5.2 Tag the code that implements REQ-SPECS-008 with `@req` in check.py (`check_change`, `_check_proposal`), capabilities.py (`resolve_delta`); verify `specworks trace` lists its code and the suite still passes

## 6. REQ-SPECS-009 Tasks

- [x] 6.1 Tag the tests that check the criteria of REQ-SPECS-009 with `@ac`, and write a test for AC-SPECS-009.3's `## Workflow follow-up` part, which must pass against the current code; verify `specworks trace` lists a test for each
- [x] 6.2 Tag the code that implements REQ-SPECS-009 with `@req` in tasks.py (`parse_tasks`, `set_done`), check.py (`_check_tasks`); verify `specworks trace` lists its code and the suite still passes

## 7. REQ-SPECS-010 Finding a capability and its next ID

- [x] 7.1 Tag the tests that check the criteria of REQ-SPECS-010 with `@ac`, and write a test for AC-SPECS-010.3, which must pass against the current code; verify `specworks trace` lists a test for each
- [x] 7.2 Tag the code that implements REQ-SPECS-010 with `@req` in capabilities.py (`resolve_ref`, `next_id`, `describe`); verify `specworks trace` lists its code and the suite still passes

## 8. REQ-SPECS-011 Finding the tags

- [x] 8.1 Tag the tests that check the criteria of REQ-SPECS-011 with `@ac`, and write a test for AC-SPECS-011.6, which must pass against the current code; verify `specworks trace` lists a test for each
- [x] 8.2 Tag the code that implements REQ-SPECS-011 with `@req` in trace.py (`scan_tags`, `scan_rule`, `glob_match`, `is_test_file`); verify `specworks trace` lists its code and the suite still passes

## 9. REQ-SPECS-012 The trace matrix

- [x] 9.1 Tag the tests that check the criteria of REQ-SPECS-012 with `@ac`, and write a test for AC-SPECS-012.2, which must pass against the current code; verify `specworks trace` lists a test for each
- [x] 9.2 Tag the code that implements REQ-SPECS-012 with `@req` in trace.py (`build_matrix`, `gaps`, `unknown_tags`, `to_markdown`); verify `specworks trace` lists its code and the suite still passes

## 10. REQ-SPECS-013 Merging at close

- [x] 10.1 Tag the tests that check the criteria of REQ-SPECS-013 with `@ac`; verify `specworks trace` lists a test for each
- [x] 10.2 Tag the code that implements REQ-SPECS-013 with `@req` in merge.py (`plan_merge`, `apply_delta`, `requirements_index`, `close_change`); verify `specworks trace` lists its code and the suite still passes

## 11. REQ-SPECS-014 Diagrams of a change

- [x] 11.1 Tag the tests that check the criteria of REQ-SPECS-014 with `@ac`; verify `specworks trace` lists a test for each
- [x] 11.2 Tag the code that implements REQ-SPECS-014 with `@req` in check.py (`_check_diagrams`); verify `specworks trace` lists its code and the suite still passes
