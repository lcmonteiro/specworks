# Inspection: add-inspect-skill

## Findings

<!-- One finding per note the reviewer left, written with
`specworks finding add <type> "<text>" --proposal "<proposal>" --artifact inspection`.
`- [ ] I<n>` while open, `- [x] I<n>` once an inspection confirmed it. -->

- [ ] I1 **code-gap** trace of a closed change compares MODIFIED blocks with today's living spec, so criteria added by later changes show as removedStillTagged (unify-check-findings lists AC-CLI-011.5, AC-FLOW-001.6, AC-FLOW-010.12, AC-FLOW-010.13, AC-FLOW-012.11, AC-FLOW-016.12, AC-FLOW-016.13) (src/specworks/specs/trace.py:249); found while inspecting unify-check-findings
  - **Proposal**: back to code: for an archived change compare with the living spec at its close commit (or skip dropped_criteria), and add a test where a later change adds a criterion
  - **Suggestion**:
    ```diff
    -        for sc in delta.dropped_criteria(req):
    +        for sc in ([] if archived else delta.dropped_criteria(req)):
    ```

## Summary

<!-- The blocks walked out of the total, and the notes written. -->
