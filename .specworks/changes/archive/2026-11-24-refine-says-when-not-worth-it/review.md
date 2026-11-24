# Review: refine-says-when-not-worth-it

Base: `origin/main`

## Findings

None.

## Changed files without tags

- `tests/test_skills.py`: wording tests for the refine skill and the refinement instruction; the change is `skip-specs` and the skills have no capability, so there is no `@ac` to tag (the tests say so in their comment).

## Summary

No drift: the refine skill (stance, step 3, step 5) and the refinement instruction in `schema.yaml` carry design.md's pinned wording verbatim, the installed copy under `.claude/skills/` matches the source with its includes expanded, and the five new tests in `tests/test_skills.py` assert each pinned phrase in the section it belongs to (full suite: 1345 passed). Nothing sent back. A candidate for a later change, already out of scope in proposal.md: the wrong `specworks abandon <ref>` form in `specworks-baseline`.
