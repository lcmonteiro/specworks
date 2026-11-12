# Inspection: unify-check-findings

## Findings

<!-- One finding per note the reviewer left, written with
`specworks finding add <type> "<text>" --proposal "<proposal>" --artifact inspection`.
`- [ ] I<n>` while open, `- [x] I<n>` once an inspection confirmed it. -->

- [ ] I1 **code-gap** validate links a V finding to its check by the check's full name, and 'changed files without tags are accounted for in review.md (base <since>)' carries the base, so a rerun with another base (main vs origin/main, or the default) never closes the old V and adds a duplicate (src/specworks/workflow/validate.py:147, src/specworks/workflow/checks.py:254; REQ-FLOW-019, AC-FLOW-019.3)
  - **Proposal**: back to code: link a V finding to a stable key of its check (the check function's name, e.g. files_accounted) instead of its display name, and add a test that reruns with another base
  - **Decision**: back to implement: test that a rerun of validate --write with another base closes the old V and adds no duplicate; code that links a V finding to a stable key of its check (the check function's name) instead of its display name

## Summary

<!-- The blocks walked out of the total, and the notes written. -->
