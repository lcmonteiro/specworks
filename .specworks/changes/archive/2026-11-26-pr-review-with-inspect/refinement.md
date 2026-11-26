# Refinement: pr-review-with-inspect

## Problem

A pull request of a specworks change is opened after close, so a reviewer
who is not the author reviews an archived change. `/specworks-inspect` helps
that reviewer walk it and keeps their notes in the archived `inspection.md`,
but nothing defines the loop around it: how the notes reach the author on
another machine, how the author learns there are notes waiting, which skill
continues, and how the reviewer learns the notes were addressed. Today the
author must already know to reopen, and reopen asks for a reason it could
read from `inspection.md`, then duplicates the notes as review findings.

## Outcomes

- The PR review process is: the author closes and pushes, the reviewer
  inspects the PR branch and pushes `inspection.md` with the notes, the author
  reopens and works the notes through review → build → done and pushes, the
  reviewer inspects again and confirms each addressed note, then approves.
- After pulling, the author sees in `specworks status`, `list --archived`,
  `context` and `/specworks-onboard` (and `/specworks-refine` step 1) that a
  closed change has inspection notes waiting for them, and is pointed to
  `/specworks-reopen <ref>`.
- After pulling the author's fix, the reviewer sees the notes waiting for
  their confirmation, and is pointed to `/specworks-inspect <ref>`; the author
  is not told to reopen again.
- `/specworks-reopen` on a change with notes waiting for the author does not
  ask why: the notes are the reason (`inspection notes I1, I2`), the phase is
  the earliest their `back to <step>` proposals need (`specify`, else
  `review`), it still asks once `Reopen <ref> at <phase>? (yes/no)`, and adds
  no `R` findings (the `I<n>` are already the findings review decides).
- Without such notes, reopen behaves as today: it asks the author why.
- `status` shows `inspection.md` as open while it has open notes (today it
  says `done` because the file exists).

## Context

**Observed:**
- `_shared/pushing.md`: `/specworks-close` and `/specworks-done` offer the
  push after close and relay the "create a pull request" link; every merge on
  `main` follows `<ref>: close`. The PR therefore holds an archived change.
- `specworks-inspect/SKILL.md`: on a closed change, notes are written to the
  archive folder's `inspection.md` (the one archive write the CLI allows),
  committed with `--message "inspect"`, never pushed; with notes it offers
  `/specworks-reopen` to whoever ran it.
- A note's lifecycle is already recorded in the file
  (`2026-11-12-unify-check-findings/inspection.md`): `- [ ] I<n>`, then
  `**Decision**` (review), `done in <step>:`, `done in review:`, then
  `confirmed in inspect:` with `- [x] I<n>`. Open + `done in review:` means
  waiting for the reviewer; open without it means waiting for the author.
- `core/changes.py:264`: reopen moves the whole folder archive → active, so
  `inspection.md` comes along; `changes.py:251` refuses when `active/<name>`
  exists, so the notes cannot be written to `active/` while closed.
- `specworks-reopen/SKILL.md` step 2 always asks the user for the reason and,
  at `review`, adds one `R` finding per problem; it never reads
  `inspection.md`.
- `specworks-review/SKILL.md:160` already treats `I<n>` findings like `V<n>`
  and routes them back to inspect.
- `cli/output.py:70` `change_dict` builds the change row of `status`, `list`
  and `context` (it adds `archived`); `workflow/findings.py:173`
  `parse_findings` parses a check artifact. `cycle` refuses archived changes;
  `context` lists active changes only; `status` marks `inspection.md` `done`
  when it exists.
- Inspection blocks no gate (architecture decision, add-inspect-skill).

**Assumed:**
- The reviewer has write access to the PR branch (same-repository PRs).
- The reviewer runs specworks and an agent with the skills installed.
- Parsing the `inspection.md` of each archived change is cheap (two exist).

## Constraints

- [hard] The PR opens after close, as today: the reviewer sees everything
  that merges, the living docs included.
- [hard] Only the author reopens; the reviewer never moves the change.
- [hard] The notes travel as the archived `inspection.md`, committed and
  pushed to the PR branch by the reviewer; never written into `active/` while
  the change is closed.
- [hard] Only the reviewer ticks an `I<n>` (`confirmed in inspect:`); the
  author's close does not wait on them (inspection stays out of the gates).
- [hard] Whose turn it is is derived from `inspection.md`, never stored.
- [soft] Reopen keeps its single phase confirmation before writing anything.

## Options

### Option A: Derive the turn from inspection.md (CLI + skills)

`change_dict` parses an archived change's `inspection.md` and reports its open
notes split by turn (author: no `done in review:`; reviewer: with it);
`status`, `list --archived` and `context` show them with the skill to run.
Onboard and refine point to it; reopen reads the author's notes as its
problem; inspect, run by a reviewer, ends with push and "request changes"
instead of offering the reopen.

- **Pros:** no new state; both sides told whose turn it is; no duplicate
  findings; uses the lifecycle already in the file.
- **Cons:** CLI change in a shared row builder; `context` reads archives.
- **Effort:** M
- **Touches:** cli, workflow, skills (inspect, reopen, onboard, refine)
- **Outcomes:** meets all six.

### Option B: A stored marker on the archived change

Inspect sets `inspection: open` in the archived `.change.yaml`; reopen or a
confirming inspect clears it.

- **Pros:** one key to read.
- **Cons:** a second source of truth that can drift from the file; does not
  tell the author's turn from the reviewer's without more state.
- **Effort:** M
- **Touches:** project, cli, skills
- **Outcomes:** meets 1, 2, 4, 5; fails 3 without a second marker.

### Option C: Only the PR (skills text only)

The process is documented in the skills; the reviewer's "request changes"
is the only signal; reopen unchanged.

- **Pros:** no CLI change.
- **Cons:** specworks shows nothing; the author retypes the notes and
  duplicates them as `R` findings.
- **Effort:** S
- **Touches:** skills
- **Outcomes:** meets 1; fails 2-6.

## Recommendation

Option A, agreed with the user: both turns reported (author → reopen,
reviewer → inspect), and reopen takes open author notes as its problem while
keeping its one phase confirmation.

## Open Questions

- Does `context` report these changes in a separate `inspected` list, or in
  `changes` marked `archived`? Recommended: a separate list, so `changes`
  keeps meaning work in flight. (who can answer: the user, at specify)
- Does inspect, run by a reviewer with notes, offer the push itself, or only
  tell the reviewer to push? (who can answer: the user, at specify)
- The PR wording the skills use (request changes, re-request review), and
  whether a fork PR (no push access) is out of scope. (who can answer: the
  user, at specify)

## Candidate Capabilities

- `cli`: modified - `status`, `list --archived` and `context` report an
  archived change's open inspection notes by turn, with the skill to run.
- `workflow`: modified - reading an archived change's inspection notes split
  by turn; `inspection.md`'s state in `status` reflects open notes.
- The skills `specworks-inspect`, `specworks-reopen`, `specworks-onboard` and
  `specworks-refine` change their text (skills have no capability yet).
