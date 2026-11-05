# Review: add-reopen-change

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **quality** src/specworks/skills/specworks-reopen/SKILL.md lines 115-116 (and the installed .claude copy) repeat the line "`specify` no finding is added: that phase's skill reads the reason from" twice, breaking the sentence in step 4 (REQ-CLI-020)
  - **Proposal**: back to code: delete the duplicated line in src/specworks/skills/specworks-reopen/SKILL.md and run uv run specworks skills to refresh the installed copy

## Changed files without tags

- `tests/support/reopen.py`: helper of the reopen tests (sample closed changes for AC-PROJ-033/034, AC-CLI-020/021), no criterion of its own.
- `tests/test_skills.py`: the skill tests are untagged by design (the skills have no capability yet); they assert the pinned wording of design.md.

## Summary

Code, specs and design agree: every REQ-PROJ-033/034, REQ-SPECS-017 and REQ-CLI-020/021 behaviour is implemented and tested, the Interfaces match design.md, and the suite passes (1065 tests). One finding: the new reopen skill repeats a line in step 4 (R1, quality), sent back to code.
