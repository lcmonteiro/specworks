# Review: clear-decision-prompts

Base: `origin/main`

## Findings

- [x] R1 **quality** Three reworded prose lines were left unwrapped (93-118 characters), and build's spec-finding options are written inline as code spans instead of the numbered block the shared rule shows (`src/specworks/skills/_shared/picking-the-change.md:10`, `src/specworks/skills/specworks-baseline/SKILL.md:64`, `src/specworks/skills/specworks-build/SKILL.md:104`)
  - **Decision**: back to code: rewrap the three paragraphs, and write build's spec-finding options as a numbered block like the other phase ends
  - done in code (cycle 2): the three paragraphs are rewrapped, build's spec-finding options are a numbered block, and the installed copies are refreshed

## Changed files without tags

- None: `specworks review` lists no untagged code or test files. The changed files are skill text (`src/specworks/skills/*/SKILL.md`, `_shared/asking-the-user.md`, `_shared/picking-the-change.md`), their installed copies (`.claude/skills/`, `.github/skills/`, `.github/prompts/`) and the change folder.

## Summary

The shared rule `asking-the-user` is included in all 12 skills, and every decision point and phase end now closes with a yes/no question or numbered options with one recommended. Baseline's hand-over kept the phrase `tests/test_skills.py` checks. One formatting finding (R1) was fixed in cycle 2.
