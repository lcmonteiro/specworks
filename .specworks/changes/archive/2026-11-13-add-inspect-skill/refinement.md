# Refinement: add-inspect-skill

## Problem

Reviewing a specworks change (or its pull request) means cross-reading the
delta specs, the design, the tests and the code by hand: which code answers a
scenario's WHEN, which test proves its THEN, and why the design chose it. No
skill guides that human review, for an open change before merge or for a
closed one after the fact, and nothing records what the reviewer found so the
flow can act on it.

## Outcomes

- `/specworks-inspect <change>` walks a change, open or closed, step by step:
  first why (from the proposal), then one scenario at a time: its WHEN with the
  code that implements it, its THEN with the test that proves it, both cut to
  the lines that matter, and the design excerpt that argues for it when there
  is one.
- Every excerpt names its source (`file:line`); on a closed change it says when
  the file changed since the close. Every step ends with the next options
  (next scenario, add a note, show more, jump to another requirement).
- A step may carry up to three one-line hints, only when there is something
  to say: a question the reviewer should ask, an unclear or ambiguous spot in
  the code or the spec, and alternative hypotheses when more than one reading
  fits. A clear scenario passes without comment.
- The reviewer's notes are kept in `inspection.md` in the change folder, in
  the findings format shared with review and validate (`I<n>`, each with where
  it sends the change). With notes, an open change goes on to
  `/specworks-review`, and a closed one to `/specworks-reopen` with
  `inspection.md` as the problem.
- Gates, validate and close behave as before: inspection is optional.

## Context

**Observed:**
- Delta specs (`specs/<capability>/spec.md`) already give each scenario as
  `Scenario: AC-... / WHEN / THEN`; tests carry `# @ac AC-...` above the test
  function, code carries `# @req REQ-...` (per requirement, not per criterion),
  so one code excerpt serves every scenario of a requirement.
- `specworks trace --change` gives requirement → criterion → task → test →
  code with `file:line`, but refuses an archived change ("archived ..., not
  active"); the archived `traceability.md` is a snapshot whose lines may be
  stale. `specworks status` already reads archived changes.
- `specworks reopen --change --reason --phase` moves a closed change back to
  the active ones; `/specworks-reopen` decides the earliest phase to redo.
- `review.md` is read by the CLI (`workflow/review.py`: `cycle`, the review
  gate, `validate`, `specworks finding add|decide|done|close`) and by the
  build, review, specify/design/test/code (back from review), validate and
  close skills. `/specworks-validate` writes no artifact today: its verdict is
  only in the conversation.
- Artifacts are declared in `src/specworks/schema.yaml` (with `optional`) and
  their templates in `src/specworks/templates/`.
- REQ-HARNESS-001 requires one harness peer per packaged skill
  (`src/specworks/harness/peers/<name>.py`), so a new skill needs a new peer.
- `/specworks-onboard` is a read-only skill beside the flow, the closest model.
- Commits are per phase (`<ref>: <phase>`), so a closed change's history is in
  git.

**Assumed:**
- The `@req`/`@ac` tags of a closed change are still in today's code, so its
  trace can be recomputed on the current tree.
- "The lines that matter" in an excerpt are a judgement the skill makes from
  the locations the CLI gives, not something the CLI computes.

## Constraints

- [hard] Depends on `unify-check-findings`: the findings format and routing
  shared by review, validate and inspect come from that change, built first.
- [hard] Inspection stays out of the gates; validate and close do not read
  `inspection.md`.
- [hard] A harness peer `inspect` for the new skill (REQ-HARNESS-001).
- [hard] On a closed change the skill shows the current code, flagging files
  changed since the close (rework would start from today's code).
- [soft] Not verbose: excerpts cut to what matters, hints only when present,
  at most three per step.
- [soft] The skill writes only `inspection.md`; decisions on the notes stay
  with `/specworks-review` and `/specworks-reopen`.

## Options

### Option A: Skill only

The skill uses `specworks trace` for an open change, and for a closed one the
archived `traceability.md` plus searching the tags itself.

- **Pros:** no CLI change beyond the `inspection` artifact.
- **Cons:** on closed changes the locations are stale or found by hand.
- **Effort:** S
- **Touches:** workflow (artifact), harness (peer)
- **Outcomes:** meets 1, 3, 4 and 5 for open changes; 1 and 2 are unreliable
  for closed ones.

### Option B: Skill + `trace` reads closed changes

`specworks trace --change` accepts an archived change (read-only), recomputes
its tags on the current code and marks the files changed since its close; the
skill extracts and filters the excerpts.

- **Pros:** reliable locations for open and closed changes from one existing
  command; onboard and reopen can use it too.
- **Cons:** a small change to `trace` and its CLI error.
- **Effort:** M
- **Touches:** specs (trace), cli (trace), workflow (artifact), harness (peer)
- **Outcomes:** meets all five.

### Option C: Skill + a dedicated `specworks inspect` command

A new command returns the ordered steps: scenario, WHEN/THEN, and the function
ranges of each test and code location.

- **Pros:** deterministic excerpts.
- **Cons:** a second way to cross specs and tags beside `trace`; filtering is
  still the skill's judgement, so little is gained.
- **Effort:** L
- **Touches:** specs, cli, workflow, harness
- **Outcomes:** meets all five.

## Recommendation

Option B: it meets every outcome with a small change to a command that
already exists, and keeps judgement (what matters, the hints) in the skill.
Agreed with the user; built after `unify-check-findings` closes.

## Open Questions

- For a `skip-specs` change (no scenarios), what does inspect walk: the diff
  guided by the tasks? (who can answer: the user, at specify)
- Does an inspection with no notes record an approval in `inspection.md`?
  (who can answer: the user, at specify)
- The shared findings format and routing (IDs, types, destinations, which
  commands read which file). (who can answer: the user, in the refinement of
  `unify-check-findings`)

## Candidate Capabilities

- `specs`: modified - the trace matrix of an archived change, with files
  changed since its close.
- `cli`: modified - `specworks trace --change` accepts an archived change.
- `workflow`: modified - the optional `inspection` artifact and its template.
- `harness`: modified - the `inspect` peer for the new skill.
- The skill `specworks-inspect` itself has no capability (skills have none yet).
