# Tasks: phase-subagents

## 1. Shared contract

- [x] 1.1 Write `src/specworks/skills/_shared/phase-subagents.md`: the fixed prompt (ref and skills folder only), proposal-before-question, the `Result: done | question | blocked` line, where each answer is written before a restart, and the fallback with no subagent tool; verify by reading it
- [x] 1.2 Add wording checks to `tests/test_skills.py`: both skills include the shared text, and it names the three `Result:` kinds; verify they fail before 2.1 and 3.1

## 2. Build

- [x] 2.1 Rework `specworks-build/SKILL.md` to run design, test, code and review each in a subagent per the shared text, with `Agent` in `allowed-tools`; verify the 1.2 checks for build pass
- [x] 2.2 Review in a build: findings written open with `**Proposal**:`, returned in one `Result: question`, each answer turned into its `**Decision**:` by the coordinator, then a fresh review subagent finishes and gates; verify by reading steps 3 and 4

## 3. Done

- [x] 3.1 Rework `specworks-done/SKILL.md`: validate in a subagent; capability registrations written by the coordinator with `specworks capability add`; the first close subagent stops after the dry run, the second starts with the fixed "merge plan approved, continue from step 4" prompt; `Agent` in `allowed-tools`; verify the 1.2 checks for done pass

## 4. Installed copies and checks

- [x] 4.1 Refresh the installed copies with `specworks skills`; verify `git diff` shows only skill files and `tests/test_skills.py` changed
- [x] 4.2 Run `specworks run test` and `specworks run lint`; verify both pass
