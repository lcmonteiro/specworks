# Tasks: add-onboarding-skill

## 1. The onboarding skill

- [ ] 1.1 [test] Add wording checks to `tests/test_skills.py` for `specworks-onboard`: the frontmatter name and description phrases, `allowed-tools` without `Write`/`Edit`, the two includes, and every phrase under **Pinned wording** in design.md; verify they fail before 1.2
- [ ] 1.2 [code] Write `src/specworks/skills/specworks-onboard/SKILL.md`: frontmatter, the read-only phase boundary, step 1 (state from `specworks context --json`, the state table and the per-phase next skill), step 2 (the primer), step 3 (answering questions in the agreed order), guardrails, all with the pinned wording; verify by reading it against design.md

## 2. README and installed copies

- [ ] 2.1 [test] Add a check that `README.md`'s Quick start holds the pinned onboarding line before step 1; verify it fails before 2.2
- [ ] 2.2 [code] Add the pinned line to `README.md`'s Quick start, just before step 1; verify by reading the README
- [ ] 2.3 [code] Refresh the installed copies with `specworks skills`; verify `git status` shows `.claude/skills/specworks-onboard/SKILL.md` and `specworks context` reports the skills current
- [ ] 2.4 [code] Run `specworks run lint`; verify it passes
