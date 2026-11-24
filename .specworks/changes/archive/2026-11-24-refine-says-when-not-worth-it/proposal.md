# Proposal: refine-says-when-not-worth-it

## Why

When exploring a request in refine shows that the request itself is not a
good idea (it duplicates something that exists, breaks a constraint, costs
more than it gives, or fixes the wrong problem), the refine skill gives the
agent no place to say so: every path leads to options for the request and on
to specify, so the objection is softened into one con among many.
(Option A of refinement.md.)

## What Changes

- `specworks-refine`, The stance: a **Candid** bullet: when the evidence says
  the request is not a good idea, say so plainly with that evidence; never
  soften it into one con among many.
- `specworks-refine`, step 3 Explore: as soon as the agent finds out, it
  stops and says "I don't think this is a good idea: <why>", then asks one
  question: go on anyway, reshape the request, or abandon it with
  `specworks abandon --change "<ref>" --reason "<why>"` (run only on the
  user's answer).
- `specworks-refine`, step 5: while the objection stands, the closing options
  add abandoning the change.
- `src/specworks/schema.yaml`, the refinement instruction: the
  Recommendation may read `Not recommended: <why>`, followed by the user's
  decision (go on, reshaped, or abandoned).
- `tests/test_skills.py` pins the new phrases; the installed copies
  (`.claude/skills/`) are refreshed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: skill text and the refinement instruction only (`specworks skip-specs`);
the skills have no capability.

## Related requirements

- REQ-FLOW-002 left: how an artifact's instruction is served is unchanged; only the refinement text changes.
- REQ-CLI-006 left: `abandon` is used as it is; the skill only names it.
- REQ-PROJ-020 left: where changes live is unchanged.
- REQ-PROJ-030 left: the event log is unchanged; `abandon` already records its event.
- REQ-PROJ-033 left: reopening is unrelated.
- REQ-FLOW-001 left: artifact states are unchanged.
- REQ-CLI-002 left: naming a change is unchanged.
- REQ-CLI-017 left: the events the commands record are unchanged.
- REQ-CLI-020 left: reopen is unrelated.

## Impact

- `src/specworks/skills/specworks-refine/SKILL.md`
- `src/specworks/schema.yaml` (refinement instruction text)
- `.claude/skills/specworks-refine/SKILL.md` (installed copy, regenerated)
- `tests/test_skills.py`
- No CLI, API or data change.

## Assumptions

- The refinement instruction in `schema.yaml` is guidance served as text, not
  behaviour a requirement pins, so it goes with the skill text under
  `skip-specs`.
- Abandoning is offered, never done, until the user answers it.

## Out of Scope

- The same rule in other phases (specify, design, review); a later change.
- A Verdict section or a gate that checks it (option C).
- The wrong `specworks abandon <ref>` form in `specworks-baseline` (the CLI
  takes `--change` and a required `--reason`); a separate fix.
