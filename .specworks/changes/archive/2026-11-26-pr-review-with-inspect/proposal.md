# Proposal: pr-review-with-inspect

## Why

A pull request holds a closed change, and the person who reviews it with
`/specworks-inspect` is not its author. Nothing tells the author, after a
pull, that the reviewer left notes, nor the reviewer that the notes were
worked; and reopen asks for a reason the notes already give, then duplicates
them as review findings.

## What Changes

- The CLI splits an `inspection.md`'s open notes by whose turn it is, from the
  routing it already has (REQ-FLOW-010): a note routed to inspect (it has
  `done in review:`) is the reviewer's turn, any other open note the author's.
- `status` of an archived change shows its open notes by turn, with the skill
  to run (`/specworks-reopen <ref>` for the author, `/specworks-inspect <ref>`
  for the reviewer), and `--json` carries them as `inspection`.
- `list --archived` shows the same per row.
- `context` gains an `inspected` list: the archived changes of the current
  module (every module with `--all`) with open notes; `changes` is unchanged.
- `status` reports `inspection.md` as `open` while it has an open note, and
  `done` once every note is confirmed (today: `done` whenever it exists).
- Skills (text only, no capability):
  - `/specworks-inspect`, on a closed change with notes: commits, offers the
    push (shared `pushing` text), then tells the reviewer to request changes
    on the PR and that the author runs `/specworks-reopen <ref>`; it no longer
    offers the reopen itself.
  - `/specworks-reopen`: when the change has notes for the author, takes them
    as the reason (`inspection notes I1, I2`) without asking why, picks the
    phase from their steps (`specify` when one is routed there, else
    `review`), still asks `Reopen <ref> at <phase>? (yes/no)` once, and adds
    no `R` findings; otherwise asks why, as today.
  - `/specworks-onboard` and `/specworks-refine` (step 1) point to the skill
    an `inspected` change waits for before new work.
  - The PR review process (author closes and pushes, reviewer inspects and
    pushes, author reopens and pushes, reviewer confirms) is written in the
    inspect skill.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `workflow`: REQ-FLOW-001 (inspection's `open` state); new REQ-FLOW-020
  (inspection notes by turn).
- `cli`: new REQ-CLI-025 (`status`), REQ-CLI-026 (`list --archived`),
  REQ-CLI-027 (`context`'s `inspected`).

## Related requirements

- REQ-FLOW-001 modified: inspection is `open` while it has an open note.
- REQ-FLOW-010 left: its routing (to inspect after `done in review:`) is what
  the turn is read from, unchanged.
- REQ-FLOW-011, REQ-FLOW-012, REQ-FLOW-019 left: gates, cycles and validate
  do not read inspection notes.
- REQ-FLOW-016 left: writing findings is unchanged.
- REQ-FLOW-018 left: inspection still blocks no gate.
- REQ-CLI-002 left: how a change is named is unchanged.
- REQ-CLI-004 left: `context` and `list` keep every field they have; the new
  fields are REQ-CLI-026 and REQ-CLI-027.
- REQ-CLI-006, REQ-CLI-012, REQ-CLI-018 left: create, commit and telemetry
  are unaffected.
- REQ-CLI-011 left: the `finding` commands are unchanged.
- REQ-CLI-017 left: no new event is recorded.
- REQ-CLI-020, REQ-CLI-021 left: `reopen` and its record are unchanged; the
  reopen skill passes the reason it builds.
- REQ-PROJ-010, REQ-PROJ-020, REQ-PROJ-024, REQ-PROJ-030, REQ-PROJ-031,
  REQ-PROJ-036 left: unrelated to inspection notes.
- REQ-PROJ-012 left: listing the archive is unchanged.
- REQ-PROJ-033, REQ-PROJ-034 left: reopen still moves the whole folder,
  `inspection.md` with it.
- REQ-SPECS-017, REQ-SPECS-018 left: trace is unchanged.
- REQ-FLOW-002, REQ-PROJ-003, REQ-PROJ-007, REQ-PROJ-025, REQ-CLI-001,
  REQ-CLI-013, REQ-CLI-019, REQ-INTEG-009, REQ-HARNESS-002, REQ-HARNESS-006,
  REQ-HARNESS-009 left: matched on "context" or "status" in another sense.

## Impact

- `src/specworks/workflow`: reading an inspection's open notes by turn;
  inspection's artifact state.
- `src/specworks/cli`: `status`, `list --archived`, `context` (`inspected`).
- Skills `specworks-inspect`, `specworks-reopen`, `specworks-onboard`,
  `specworks-refine`, and their installed copies; `tests/test_skills.py` for
  wording.
- JSON: new keys `inspection` (status, list rows, `inspected` rows) and
  `inspected` (context); a new artifact state `open`.

## Out of Scope

- Pull requests from forks, where the reviewer cannot push the branch.
- Posting notes as PR comments, or any GitHub/GitLab API call.
- Opening the PR before close; gates reading inspection notes.
- Recording an approval when an inspection leaves no notes.
- A review in progress before the reviewer pushes (it lives on the PR).
