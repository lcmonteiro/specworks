# Tasks: review-indented-checkboxes

## 1. Checkboxes outside any finding

- [ ] 1.1 Write a failing test for AC-FLOW-010.5 in `tests/test_build_cycle.py` (an indented `- [ ]` under a non-finding bullet is reported; under a finding it isn't) and a gate check in `tests/test_review_phase.py` (the review gate fails with `--allow-open`), tagged `@ac`; verify they fail because nothing is reported
- [ ] 1.2 In `parse_review`, report a checkbox that isn't a finding whenever no finding's block is open, whatever its indentation (REQ-FLOW-010) tagged `@req REQ-FLOW-010`; verify the 1.1 tests and the existing AC-FLOW-010.x tests pass
