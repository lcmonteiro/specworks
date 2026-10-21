# Review: phase-subagents

Base: `origin/main`

## Findings

- [ ] R1 **code-gap** a restarted phase subagent is not told to use an answer already on disk, so design (and a code pause) asks its question again forever; design.md has no mark for an API agreed rather than proposed (`src/specworks/skills/_shared/phase-subagents.md:12`)
  - **Decision**: back to code: add to the fixed prompt "When the answer to a question the skill would ask is already on disk, use it and go on; do not ask it again."; the design row of the table says the subagent writes `Proposed: waiting for the user's agreement` under `## Interfaces` and the coordinator replaces it with `Agreed with the user`; a wording test in `tests/test_skills.py` checks the prompt carries the sentence

## Changed files without tags

- None: `specworks review` lists no untraced source or tests (skill text and untagged wording checks; the change skips specs).

## Summary

The build and done skills run each phase in a subagent through the shared
`_shared/phase-subagents.md`. One finding, R1, goes back to code: a
restarted phase must use the answer already on disk instead of asking again.
