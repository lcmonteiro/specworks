# Review: commit-phase-and-half

Base: `origin/main`

## Findings

- [ ] R1 **design-gap** specworks-reopen still commits with `--message "<ref>: reopen"`, written for the old whole-subject `--message`: under REQ-PROJ-036 the subject becomes `<ref>: <phase> - <ref>: reopen`, the ref doubled; design.md "Skill text" pins inspect but not reopen, and tests/test_skills.py:892 pins the old wording (`src/specworks/skills/specworks-reopen/SKILL.md:100`)
  - **Proposal**: back to design: add specworks-reopen to the Pinned wording (`--message "reopen"`, and no `--message "<ref>: reopen"`); the test half updates the reopen pin in tests/test_skills.py, the code half edits the reopen skill line and refreshes .claude/skills
  - **Decision**: back to design: pin `--message "reopen"` for specworks-reopen (and no `--message "<ref>: reopen"`); the test half updates the pin in tests/test_skills.py and the code half edits the skill and refreshes .claude/skills
  - done in design: design.md "Skill text" pins `--message "reopen"` for specworks-reopen, and no `--message "<ref>: reopen"`; the API is unchanged
  - done in implement: code half: specworks-reopen commits the move with --message "reopen" (no "<ref>: reopen"); .claude/skills refreshed
- [x] R2 **quality** specworks-inspect commits inspection.md with `specworks commit --change "<ref>" --message "inspect"` (no `--half`): for an open change still in implement REQ-PROJ-036 refuses it ("say which half"), though inspect is not a half (`src/specworks/skills/specworks-inspect/SKILL.md:176`)
  - **Proposal**: accepted: inspect of an open change normally runs after review (before merge), and the refusal names both flags and stages nothing; a half for inspect would be a new feature
  - **Decision**: accepted: inspect of an open change normally runs after review; the refusal names both flags and stages nothing

## Changed files without tags

- `tests/test_skills.py`: the skill-text tests of design.md's Pinned wording (tasks 4.1); the skills have no capability yet, so these tests are untagged, as CLAUDE.md says.

## Summary

All 1339 tests pass; every requirement has tagged code and every criterion a test that asserts its THEN, and the code follows design.md's Interfaces and Decisions (`phase_subject`, `commit_phase(message=, half=)`, `commit --half`, the merge's `-m <subject>` on both paths). Two open findings, both about skills that pass `--message`: specworks-reopen still writes a whole subject (R1, back to design), and inspect of an open change in implement is refused without a half (R2, proposed accepted).
