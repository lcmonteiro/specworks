# Inspection: add-inspect-skill

## Findings

<!-- One finding per note the reviewer left, written with
`specworks finding add <type> "<text>" --proposal "<proposal>" --artifact inspection`.
`- [ ] I<n>` while open, `- [x] I<n>` once an inspection confirmed it. -->

- [x] I1 **code-gap** trace of a closed change compares MODIFIED blocks with today's living spec, so criteria added by later changes show as removedStillTagged (unify-check-findings lists AC-CLI-011.5, AC-FLOW-001.6, AC-FLOW-010.12, AC-FLOW-010.13, AC-FLOW-012.11, AC-FLOW-016.12, AC-FLOW-016.13) (src/specworks/specs/trace.py:249); found while inspecting unify-check-findings
  - **Proposal**: back to code: for an archived change compare with the living spec at its close commit (or skip dropped_criteria), and add a test where a later change adds a criterion
  - **Suggestion**:
    ```diff
    -        for sc in delta.dropped_criteria(req):
    +        for sc in ([] if archived else delta.dropped_criteria(req)):
    ```
  - done in specify: added AC-SPECS-018.4 and AC-SPECS-018.5 to REQ-SPECS-018: removed criteria of a closed change come from the living spec at its close commit, none without it
  - done in design: added the stub living_spec_at(ws, change, cap, commit) -> str | None in specs/trace.py (the living spec at the close commit) and its typed entry under Interfaces
  - done in implement: code: for an archived change, Analysis.rows compares its MODIFIED and REMOVED blocks with the living spec at the close commit's parent (living_spec_at), and reports no removed criterion without that commit (trace.py _specs_at_close)
  - done in review: checked: for an archived change Analysis.rows compares MODIFIED/REMOVED blocks with the living spec at the close commit's parent (trace.py _specs_at_close, living_spec_at); AC-SPECS-018.4/.5 tests pass, and specworks trace --change unify-check-findings --json now reports no removedStillTagged
  - confirmed in inspect: the trace of a closed change compares with the living spec at the close commit's parent (trace.py:416-434); test_ac_specs_018_4 checks a later criterion is not removed and the left-out one still is (9 passed); trace of unify-check-findings shows removedStillTagged []

## Summary

<!-- The blocks walked out of the total, and the notes written. -->
