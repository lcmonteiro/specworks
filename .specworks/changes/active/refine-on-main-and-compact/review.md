# Review: refine-on-main-and-compact

Base: `origin/main`

## Findings

- [x] R1 **quality** The new section says "before you read or run anything", yet its second stop runs `git status --short --branch`; the intro contradicts the stop it introduces (src/specworks/skills/specworks-refine/SKILL.md:34)
  - **Proposal**: Reword the intro to "before step 1" (e.g. "Two stops, in this order, before step 1. Each can be answered \"no\", and the skill then goes on."); the pinned phrases B1-B11 are unchanged
  - **Decision**: back to code: reword the intro of ## Before step 1 to 'before step 1'
  - done in code: intro of ## Before step 1 reworded to 'before step 1'; installed copy refreshed
  - confirmed in review: Intro of ## Before step 1 now says 'before step 1' in the packaged skill and the installed copy; B1-B11 intact, 1007 tests pass

## Changed files without tags

- `tests/test_skills.py`: wording tests for the refine skill (B1-B11 in design.md); the change is `skip-specs`, so there are no `@ac` criteria to tag.

## Summary

Skill text, wording tests and one architecture decision; the suite passes (1007) and B1-B11 are all present in the packaged skill, the installed copy matches, no spec or API drift. R1 (intro contradicting the git status stop) was reworded and is closed.
