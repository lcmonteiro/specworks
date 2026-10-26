# Design: drop-review-finish-run

## Context

Skill text only (`skip-specs`): see proposal.md. The change rewrites step 3
of `src/specworks/skills/specworks-build/SKILL.md` and the wording check in
`tests/test_skills.py`; no Python code changes.

## Interfaces

None: the change edits skill text and a test's expected wording; no class,
function, CLI command or data shape is added or changed.

## Decisions

### Task 1.2 waits for the test half's wording check

The code half rewrote step 3 of `specworks-build/SKILL.md` and refreshed the
installed copies; lint and typecheck pass. The suite has one failure,
`tests/test_skills.py::test_build_gates_the_review_itself_when_every_finding_is_accepted`,
the old wording check ("decided `accepted`") that task 1.1 [test] replaces.
Task 1.2's verification ("the 1.1 check passes", `specworks run test`
passes) can only pass once the test half is merged, so 1.2 is not ticked and
`gate code` does not pass yet.

Agreed with the user. Rerun the code half after the
test half's worktree is merged; it then verifies, ticks 1.2 and gates.
