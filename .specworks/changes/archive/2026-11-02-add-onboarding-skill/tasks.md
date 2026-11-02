# Tasks: add-onboarding-skill

## 1. The onboarding skill

- [x] 1.1 [test] Add wording checks to `tests/test_skills.py` for `specworks-onboard`: the frontmatter name and description phrases, `allowed-tools` without `Write`/`Edit`, the two includes, and every phrase under **Pinned wording** in design.md; verify they fail before 1.2
- [x] 1.2 [code] Write `src/specworks/skills/specworks-onboard/SKILL.md`: frontmatter, the read-only phase boundary, step 1 (state from `specworks context --json`, the state table and the per-phase next skill), step 2 (the primer), step 3 (answering questions in the agreed order), guardrails, all with the pinned wording; verify by reading it against design.md
- [x] 1.3 [test] Add `specworks-onboard` to the exclusion list of `test_skills_pick_the_change_by_one_shared_rule` in `tests/test_skills.py` (it picks no change, like start and adopt; design.md "The skill picks no change"); verify the test passes for every other skill

## 2. README and installed copies

- [x] 2.1 [test] Add a check that `README.md`'s Quick start holds the pinned onboarding line before step 1; verify it fails before 2.2
- [x] 2.2 [code] Add the pinned line to `README.md`'s Quick start, just before step 1; verify by reading the README
- [x] 2.3 [code] Refresh the installed copies with `specworks skills`; verify `git status` shows `.claude/skills/specworks-onboard/SKILL.md` and `specworks context` reports the skills current
- [x] 2.4 [code] Run `specworks run lint`; verify it passes
