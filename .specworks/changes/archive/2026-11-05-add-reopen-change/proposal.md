# Proposal: add-reopen-change

## Why

After `specworks close` a change is archived with its specs already merged, and CI, a review or a conflicting PR can still ask for more work. Today the only way back is a new change, which loses the history and leaves the old name taken. The feedback can also change what is wanted, not only the code, so the way back must reach any phase.

## What Changes

- New command `specworks reopen --change <ref> --reason "<why>" [--phase <phase>]`: it moves an archived (closed) change back to `active/`, records the reason, and sets the phase (default `review`; any phase but `done`). It touches no git state and no living doc.
- The reason, the time and the starting phase are kept in the change's metadata as a `reopened` list, so reopening twice keeps both records. `status` shows the latest reason, and `--json` carries every record.
- A reopened change can be closed again: an ID that a History line of `requirements.md` attributes to this very change is its own, so check accepts an ADDED block the living spec already has (and a REMOVED ID already gone), and the merge replaces it in place, counted as MODIFIED in History. IDs of other changes keep today's errors, and the "modified after this change started" warning ignores the change's own earlier close.
- `status` is no longer the only command that can name an archived change: `reopen` does too.
- New skill `/specworks-reopen`: takes the problem from the user (or asks for it), decides the phase (`refine`, `specify`, or `review` with a finding), says it in one line, asks for confirmation, then runs `specworks reopen` and, for `review`, `specworks finding add`.
- `/specworks-refine` and `/specworks-specify` read the latest reopen reason from `specworks status` as the problem to start from.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: reopening an archived change (move back, refusals, all or nothing) and the reopen record in its metadata.
- `specs`: a change's own IDs from an earlier close (check, merge, warning); REQ-SPECS-006 and REQ-SPECS-013 are modified to defer to it.
- `cli`: the `reopen` command, `status` showing the reopen record, and naming an archived change (REQ-CLI-002 modified to allow `reopen`).

## Related requirements

- REQ-PROJ-010 left: an archived name stays refused for a new change; reopen is the way back, so the rule is unchanged.
- REQ-PROJ-011 left: `done` is still reached only through close; reopen refuses it like `phase` does.
- REQ-PROJ-012 left: listing the archive is unchanged; a reopened change simply leaves it.
- REQ-PROJ-020 left: the active and archive folders are unchanged.
- REQ-PROJ-023 left: reopen reuses the dirty record, taken before the move.
- REQ-PROJ-024 left: committing the reopened change works as written; a CLI scenario checks it holds the archive deletions.
- REQ-PROJ-030 left: `events.jsonl` moves with the folder; recording a `reopen` event is out of scope.
- REQ-PROJ-031 left: the trace ID comes from the creation time, which reopen keeps.
- REQ-SPECS-006 modified: its ADDED and REMOVED checks defer to the change's own IDs, and its "modified after this change started" warning skips the change's own close.
- REQ-SPECS-010 left: the next ID already counts History IDs, so a reopened change never reuses one.
- REQ-SPECS-013 modified: the merge replaces an own ADDED block in place and skips an own REMOVED ID already gone.
- REQ-CLI-002 modified: `reopen` names an archived change as `status` does.
- REQ-CLI-006 left: `abandon` stays as it is; an abandoned change is not reopened.
- REQ-CLI-017 left: `reopen` records no event for now (out of scope).

## Impact

- Code: `src/specworks/core/changes.py` (reopen, the `reopened` record in `Change`), `src/specworks/specs/capabilities.py`, `check.py` and `merge.py` (own IDs), `src/specworks/cli/changes.py` and `output.py` (the command and the status output).
- Skill: new `src/specworks/skills/specworks-reopen/SKILL.md`, installed with `specworks skills`; `tests/test_skills.py` (generic skill checks and the new skill's wording).
- Data: `.change.yaml` gains an optional `reopened` list; old metadata reads as having none.
- No new dependency; git is not used by reopen.

## Out of Scope

- Reopening an abandoned change: it was dropped, not finished.
- Unmerging the living docs on reopen (needs git history, breaks after a squash or rebase).
- Git operations: switching to the change's branch, rebasing, pushing or opening the PR.
- Telemetry: no `reopen` event and no change to the Langfuse push.
- Making the skills a capability, or documenting them in the living specs.
- Choosing the phase in the CLI: the skill decides it; the CLI only takes `--phase`.

## Assumptions

- A re-merged ADDED block is counted as MODIFIED in the second History line, so History says what each close did to the living spec.
- `status` shows the latest reopen reason in its text and every record under `--json`.
- Own IDs are recognised from History alone: archived names stay taken, so only a reopened change can have History lines under its ref.
