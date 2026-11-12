# Proposal: add-inspect-skill

## Why

Reviewing a specworks change (or its pull request) means cross-reading its
specs, design, tests and code by hand, and nothing records what the reviewer
found so the flow can act on it. With check findings now shared by review and
validate (`unify-check-findings`), a guided human inspection can walk a
change scenario by scenario and leave its notes as findings the flow follows.

## What Changes

- A new skill, `/specworks-inspect <change>`, for an open or a closed change:
  - first why (from the proposal), then one scenario at a time: its WHEN with
    the code that implements it, its THEN with the test that proves it, both
    cut to the lines that matter, and the design excerpt that argues for it;
  - every excerpt names its `file:line`, and on a closed change says when the
    file changed since the close;
  - up to three one-line hints per step, only when there is something to say
    (a question to ask, an unclear or ambiguous spot, alternative hypotheses);
  - the blocks (scenarios, tasks, or a doubt spanning several) are walked
    from the most to the least uncertain and important, each step saying in
    one line why it is where it is (uncertainty: hints, a weak-looking test,
    code changed since the close, a design decision not obviously followed;
    importance: ADDED or MODIFIED behaviour, error and security paths, how
    much code depends on it);
  - every step ends with the next options (next block, add a note, show
    more, come back later, jump to a requirement, stop here);
  - a circle the reviewer breaks when they want: after the last block it
    returns to the deferred ones (`come back later`), with what was learned
    since, until none is left or the reviewer stops; stopping is a normal
    end, and the summary says how many blocks were walked out of how many;
  - for a change marked skip-specs, it walks the tasks instead, each with the
    part of the diff that carries it out.
- A third check artifact, **inspection** (`inspection.md`, letter `I`,
  optional, blocking no gate). The skill writes it only when the reviewer
  leaves notes; an inspection without notes writes nothing (the human review
  is its own record, e.g. the pull request's approval).
- Inspection findings follow the flow like any other: their type or
  `back to <step>:` routes them; a new type `question` goes to review; after
  `done in review:` they wait for inspect, which confirms and closes them on
  its next run. With notes, an open change goes on to `/specworks-review`, a
  closed one to `/specworks-reopen` with inspection.md as the problem.
- `specworks trace` reads a closed change (without `--write`), from its
  delta specs and the current code's tags, and marks the locations whose file
  changed since the close.
- `specworks finding` writes inspection findings of a closed change into its
  archive folder; every other write to an archived change is still refused.
- A harness peer `inspect` for the new skill (REQ-HARNESS-001 asks one per
  skill).

## Capabilities

### New Capabilities

- None

### Modified Capabilities

- `workflow`: REQ-FLOW-001 (inspection in the artifact list), REQ-FLOW-010
  (`I<n>`, `question`, back to inspect after review), REQ-FLOW-012 (a
  finding waiting for inspect starts no cycle), REQ-FLOW-016 (`confirmed in
  inspect:`), REQ-FLOW-018 (inspection declared, blocking no gate).
- `specs`: new REQ-SPECS-018, the trace of a closed change.
- `cli`: REQ-CLI-002 (`trace` and inspection `finding` on an archived
  change).

## Related requirements

- REQ-FLOW-001 modified
- REQ-FLOW-010 modified
- REQ-FLOW-012 modified
- REQ-FLOW-016 modified
- REQ-FLOW-018 modified
- REQ-CLI-002 modified
- REQ-SPECS-012 left: the trace of an active change is unchanged; REQ-SPECS-018 adds the closed one
- REQ-FLOW-011 left: the review gate reads only the artifacts that block it (REQ-FLOW-018 decides inspection blocks none)
- REQ-FLOW-013 left: validate reads only the artifacts that block it, likewise
- REQ-FLOW-019 left: validate writes only validation.md
- REQ-CLI-011 left: `--artifact inspection` is a check artifact like any other
- REQ-CLI-020 left: reopen already takes a reason; the skill passes inspection.md as the problem
- REQ-CLI-004 left: `list --archived` already lists closed changes to pick from
- REQ-PROJ-012 left: archived changes are listed as before
- REQ-PROJ-033 left: reopening moves the archive folder back, inspection.md with it
- REQ-HARNESS-001 left: it already asks one peer per packaged skill; the new peer follows it
- REQ-FLOW-009, REQ-FLOW-015, REQ-CLI-006, REQ-CLI-012, REQ-CLI-018, REQ-CLI-019, REQ-INTEG-009, REQ-PROJ-010, REQ-PROJ-020, REQ-PROJ-024, REQ-PROJ-030, REQ-PROJ-031, REQ-PROJ-034, REQ-SPECS-003 left: matched only by the words "trace", "archived" or "traceability"

## Impact

- `src/specworks/schema.yaml` (the `inspection` artifact),
  `src/specworks/templates/inspection.md`.
- `src/specworks/workflow/findings.py` (`question`, the step after review),
  `cycle.py` (waiting for inspect).
- `src/specworks/specs/trace.py` (an archived change, changed since close).
- `src/specworks/cli/` (`trace` and `finding` on an archived change).
- `src/specworks/skills/specworks-inspect/` (new), the review skill (closing
  only its own findings is unchanged; it marks inspection findings
  `done in review:`), `src/specworks/harness/peers/inspect.py`;
  `tests/test_skills.py`.

## Out of Scope

- Recording an approval when the inspection has no notes.
- Making inspection a gate, or required before close.
- Changing what reopen decides: the skill hands it inspection.md.
- The four small clean-ups left by `unify-check-findings` (a `fix-` change).
