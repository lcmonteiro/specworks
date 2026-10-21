# Review: track-suspected-bugs

Base: `origin/main`

## Findings

- [x] R1 **quality** Baseline step 4 says "Write nothing else in it" right after "Write its `refinement.md`", so "it" reads as the refinement rather than the bug's change folder (`src/specworks/skills/specworks-baseline/SKILL.md:148`)
  - **Decision**: back to code: say "Write nothing else in that change"
  - done in code (cycle 2): step 4 now reads "Write nothing else in that change"; installed copies refreshed

## Changed files without tags

- None: `specworks review` lists no untagged code or test files. The changed files are skill text (`src/specworks/skills/specworks-{baseline,adopt}/SKILL.md`), their installed copies (`.claude/skills/`, `.github/skills/`, `.github/prompts/`) and the change folder.

## Summary

The baseline skill now makes a `fix-<name>` change with a `refinement.md` for each confirmed bug and, after the last capability, hands over to the loop refine → specify → build → done; adopt shows the same closing loop. One wording finding (R1) was fixed in cycle 2.
