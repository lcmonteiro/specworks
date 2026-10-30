# Design: add-start-skill

## Context

See proposal.md. Packaged skills are discovered from the folders under
`src/specworks/skills/` (`specworks skills` installs every one, and
`tests/test_skills.py` iterates `packaged_skills()`), so a new skill folder
needs no registration in Python code.

## Goals / Non-Goals

**Goals:**
- A new skill file on today's CLI commands (`init`, `module add`,
  `capability add`, `context`).

**Non-Goals:**
- Any CLI or library change (Options B and C of the refinement).

## Decisions

### No code API

The skill is Markdown text read by the agent; it calls only existing
commands. The only Python touched is `tests/test_skills.py`, which adds
`specworks-start` to the skills excluded from the shared change-picking
rule (next to `specworks-refine`, `specworks-adopt`, `specworks-baseline`).

**Code half (agreed with the user)**: the skill is
written and installed, but until that exclusion (task 1.1, the test half)
is in, the existing `test_skills_pick_the_change_by_one_shared_rule
[specworks-start]` fails: the new skill creates its project and picks no
change. So task 1.2's verification ("the 1.1 checks and `specworks run
test` pass") and the code gate's suite check can only pass once the test
half is merged. Proposed: leave 1.2 open in the code half, and tick it
(and re-run `gate code`) after the test half's worktree is merged and the
suite is green; the code half does not edit the test. After the merge,
`test_start_ends_by_handing_over_to_refine` expected the hand-over with
backticks; the skill writes its closing options in a code block as every
skill does, so the test is fixed (task 1.3), not the skill (agreed with the
user).

## Interfaces

None: the change adds a packaged skill (Markdown text, task 1.2) and a README line; no public class, function or CLI command is added or changed.

## Diagrams

No structural change.

## Risks / Trade-offs

- [the agent judges "already has code" by reading the files] -> the skill
  names what does not count (docs, licence, git files) and hands anything
  else to `/specworks-adopt`.
