# Design: refine-on-main-and-compact

## Context

Skill text, tests and docs only; see proposal.md. `tests/test_skills.py`
checks skill wording verbatim (`raw_skill_file` folds line wraps into
spaces), so the test and code halves share the phrases below.
`src/specworks/skills/specworks-refine/SKILL.md` starts at step 1 today
(`specworks context --json`). `specworks new` creates the change's branch from
HEAD and reports `startedFrom` afterwards (REQ-PROJ-018, REQ-PROJ-019).

## Goals / Non-Goals

**Goals:**
- Refine asks to compact a conversation that already holds earlier work, then
  asks to start from the base branch, before it reads or runs anything.
- Both stops can be answered "no" and the skill goes on.

**Non-Goals:**
- Any CLI, config or schema change.
- The other phase skills.

## Decisions

### A section before step 1, not a numbered step

The two stops are a `## Before step 1` section between the stance and
`## Steps`, so the step numbers, `step()` in the tests and the references
from other skills stay as they are. The section is not a shared include: only
refine carries it.

### Compact is asked only when earlier work exists

A skill cannot run `/compact`, and compacting after the skill has started
would summarise away its own instructions. So refine asks first and, on yes,
stops and tells the user to compact and re-run. "Earlier work" is anything
before the request except a summary left by `/compact`, so the re-run is not
asked again and there is no loop. Alternatives (refinement.md): always ask
(the user answers no after compacting), or only a note (easy to ignore).

### The branch is read with `git status`, switched with `git switch`

`git status --short --branch` is already pre-approved and shows the branch
and any changes in one call. `git switch <base>` is not pre-approved
(`allowed-tools` is unchanged), so the user approves it when it runs. The
base branch is `main`, or `master` when the repository has no `main` (as
`BASE_CANDIDATES` in `src/specworks/workflow/review.py`). With a changed
working tree the skill never switches: it says so, stays and asks nothing.
"No" stays too, which covers continuing a change on its own branch and
stacking on purpose.

### Pinned wording

The test half asserts these and the code half writes them, verbatim (after
folding line wraps), all in `src/specworks/skills/specworks-refine/SKILL.md`
unless noted:
- B1: the heading `## Before step 1`, before `## Steps`.
- B2: `ask "Compact the conversation first? (yes/no)"`
- B3: ``anything before this request except a summary left by `/compact` ``
- B4: ``tell the user to run `/compact`, then `/specworks-refine` again with the same request, and stop``
- B5: `A new or just-compacted conversation goes straight on, without asking.`
- B6: `git status --short --branch`
- B7: `ask "You are on <branch>, not <base>. Switch to <base>? (yes/no)"`
- B8: `git switch <base>`
- B9: `When the working tree has changes, say so, stay on the branch and ask nothing.`
- B10: order: B2 before B7, and B7 before `## Steps`.
- B11: no other packaged skill contains B2 or B7.

`docs/architecture.md` (Architectural decisions):
- D1: `**Refine starts clear and from the base branch**`

## Interfaces

None: no API changes; only skill text, a test file and a docs entry.

## Diagrams

No structural change.

## Risks / Trade-offs

- [The agent misjudges "earlier work"] -> a wrong yes costs one `/compact`, a
  wrong no costs nothing; the user can always answer no.
- [Switching to the base branch loses the user's place] -> it is asked, never
  forced, and a changed working tree blocks it.

## Open Questions

None.
