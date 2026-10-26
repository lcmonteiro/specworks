# Tasks: drop-review-finish-run

## 1. Build step 3 without the finish run

- [ ] 1.1 [test] Update the build-skill wording check in `tests/test_skills.py`: step 3 says the first run ticks earlier-cycle findings, the coordinator runs `specworks gate review --change "<ref>" --allow-open` itself after writing the Decisions, and no "fresh review subagent" runs after them; verify it fails before 1.2
- [ ] 1.2 [code] Rewrite step 3 of `specworks-build/SKILL.md` as in the proposal (ticking in the first run, the coordinator gating after the Decisions, fixing its own Decision line on a gate failure, the accepted-only special case removed); refresh the installed copies with `specworks skills`; verify the 1.1 check passes and `specworks run test` and `specworks run lint` pass
