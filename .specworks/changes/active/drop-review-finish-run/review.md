# Review: drop-review-finish-run

Base: `origin/main`

## Findings

- [ ] R1 **code-gap** The general "on `Result: question`" rule still starts a fresh review subagent after the decisions, against the new step 3 (`src/specworks/skills/specworks-build/SKILL.md:75`, `src/specworks/skills/_shared/phase-subagents.md:27`)
  - What happens: step 3 now says that once every `**Decision**:` line is written the coordinator runs `specworks gate review --change "<ref>" --allow-open` itself and "no second review subagent runs". But step 2 still says, for every step of the cycle including `review`, "on `Result: question`, ask, write the answer to disk and start a fresh subagent for the same step", and the shared "Phases in subagents" text (included in the build skill) says "Write the answer where the next run of the phase reads it, then start a fresh subagent for the same phase with the same prompt", with a table row "review: each finding". A coordinator following steps 1-2 literally starts exactly the run this change drops; only step 3, read later, says otherwise.
  - The proposal and design say only step 3 changes, and the refinement notes `_shared/phase-subagents.md` as unchanged; neither considered these two generic sentences.
  - **Proposal**: back to code: in `specworks-build/SKILL.md` step 2, make the `Result: question` sentence point to step 3 for review (e.g. "...and start a fresh subagent for the same step (for review, step 3 says what follows instead)"); leave `_shared/phase-subagents.md` as it is (it is also included in `specworks-done`, and step 3 is the build's own exception), refresh the installed copies with `specworks skills`; no spec, design or test change.
  - **Decision**: back to code: in `specworks-build/SKILL.md` step 2, make the `Result: question` sentence point to step 3 for review; also add the same exception to the "start a fresh subagent for the same phase" line in `_shared/phase-subagents.md` (review in a build: see its step 3); refresh the installed copies with `specworks skills`; no spec, design or test change (agreed with the user)

## Changed files without tags

None: `specworks review` lists no untracedSource or untracedTests. The skill
copies (`src/specworks/skills/specworks-build/SKILL.md`, `.claude/skills/`,
`.github/skills/`, `.github/prompts/`) are Markdown and are not scanned for
tags; their change is task 1.2 (`skip-specs`). `tests/test_skills.py` changed
only in the build-skill wording check (task 1.1).

## Summary

Cycle 1: the suite passes (620 tests) and the step 3 rewrite and its wording
check match the proposal. One code-gap (R1): step 2's generic "start a fresh
subagent for the same step" after a question still contradicts the new step 3
for review; proposed back to code (one sentence in step 2). No spec or design
change.
