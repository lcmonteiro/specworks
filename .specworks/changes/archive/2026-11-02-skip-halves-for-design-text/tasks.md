# Tasks: skip-halves-for-design-text

## 1. Reading and writing a design-only finding

- [x] 1.1 Add `Finding.design_only` (default False) and its `designOnly` key in `Finding.to_dict()` in `src/specworks/workflow/review.py` (REQ-FLOW-010); verify it builds and the existing tests pass
- [x] 1.2 [test] Write failing tests for AC-FLOW-010.8 in `tests/test_review_phase.py`, tagged `@ac AC-FLOW-010.8`: routed to design, then to review after `done in design:`; plain `back to design:` still goes to implement; verify they fail for the right reason
- [x] 1.3 [test] Write failing tests for AC-FLOW-016.7 in `tests/test_findings.py`, tagged `@ac AC-FLOW-016.7`: the design-only Decision is written and routed to design; `back to code only:` is refused with the pinned `DECISION_FORM` and review.md is unchanged; verify they fail for the right reason
- [x] 1.4 [code] Read `back to design only:` and route it to review after `done in design:` (REQ-FLOW-010), and accept it in `DECISION_RE`/`DECISION_FORM` with the pinned wording (REQ-FLOW-016), tagged `@req`; verify with lint and `specworks finding decide` on a sample change

## 2. The cycle

- [x] 2.1 [test] Write failing tests for AC-FLOW-012.7 in `tests/test_build_cycle.py`, tagged `@ac AC-FLOW-012.7`: design-only findings alone (before and after `done in design:`), with a code finding, and with a plain `back to design:` finding; verify they fail for the right reason
- [x] 2.2 [code] Add the halves for design only when a finding is not design-only, in `next_cycle` (REQ-FLOW-012), tagged `@req REQ-FLOW-012`; verify with lint and `specworks cycle` on a sample change

## 3. Skills

- [x] 3.1 [test] Add wording checks to `tests/test_skills.py` for the pinned review and build wording in design.md (REQ-FLOW-012); verify they fail before 3.2
- [x] 3.2 [code] Add the pinned wording to `specworks-review/SKILL.md` (proposing `back to design only:`) and `specworks-build/SKILL.md` (the cycle rules and the description), then refresh the installed copies with `specworks skills` (REQ-FLOW-012); verify `specworks context` reports the skills current and `specworks run lint` passes
