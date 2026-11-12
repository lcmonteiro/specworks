# Proposal: unify-check-findings

## Why

Only review leaves findings the flow can follow. A validate FAIL lives only in
the conversation, so the phase the change goes back to gets no input, and the
upcoming inspect step (`add-inspect-skill`) has nowhere to write. The check
steps should share one model: each writes its own artifact with findings in
one format, the phases read them, and the step that found a finding closes it.

## What Changes

- The schema declares which artifacts are **check artifacts**: each has an ID
  letter and the gates its open findings block. Review (`R`, blocks the review
  and validate gates) and a new optional artifact **validation** (`V`,
  `validation.md`, blocks the validate gate) are declared.
- Findings are read the same way in every check artifact (types, routes,
  `done in`), with its own letter; `back to review:` becomes a route.
- `specworks finding add` takes `--artifact <check artifact>` (default
  `review`); `decide`, `done` and `close` find the artifact from the ID's
  letter.
- `specworks cycle` reads the open findings of every check artifact, and says
  the change's next state: the phase its findings start at, or, with none
  open, the phase after the current one.
- `specworks validate --write` writes `validation.md`: one `V` finding per
  failed blocking check, routed to the phase that fixes it, ticking the ones
  it wrote before whose check now passes and leaving the others alone; a PASS
  writes `None.`; the verdict and the warnings go in its Summary, warnings
  never as findings. Without `--write`, validate and `gate validate` write
  nothing, as before.
- Validate fails while `validation.md` has an open finding; the review gate
  ignores open `V` findings.
- Skills: validate writes `validation.md` (CLI findings, then its own with
  `finding add --artifact validation`) and commits it; review, build, reopen
  and the shared back-from-review text read and mark findings of every check
  artifact.

## Capabilities

### New Capabilities

- None

### Modified Capabilities

- `workflow`: REQ-FLOW-001 (validation in the artifact list), REQ-FLOW-010
  (findings of any check artifact, `back to review:`), REQ-FLOW-011 (other
  artifacts' findings do not block review), REQ-FLOW-012 (cycle over all check
  artifacts, next state), REQ-FLOW-013 (open V findings fail validate; writes
  only with `--write`), REQ-FLOW-016 (writing findings to any check artifact);
  new: check artifacts declared in the schema, writing validation.md.
- `cli`: REQ-CLI-011 (`finding add --artifact`, the artifact found from the
  ID); new: `validate --write`.

## Related requirements

- REQ-FLOW-001 modified
- REQ-FLOW-010 modified
- REQ-FLOW-011 modified
- REQ-FLOW-012 modified
- REQ-FLOW-013 modified
- REQ-FLOW-016 modified
- REQ-CLI-011 modified
- REQ-FLOW-002 left: instructions already serve any artifact in the schema, validation included
- REQ-FLOW-003 left: gates in common are unchanged
- REQ-FLOW-009 left: the drift report does not read findings
- REQ-FLOW-017 left: which tests the review gate runs is unchanged
- REQ-CLI-007 left: close runs validate, so an open V finding refuses close through REQ-FLOW-013
- REQ-CLI-017 left: the `finding`, `cycle` and `validate` events keep their fields
- REQ-PROJ-001 left: finding the project config, matched by the word "finding" only
- REQ-PROJ-011 left: the phases are unchanged
- REQ-SPECS-010 left: matched by the word "finding" only
- REQ-SPECS-011 left: matched by the word "finding" only
- REQ-SPECS-016 left: matched by the word "finding" only
- REQ-HARNESS-001 left: no skill is added or removed

## Impact

- `src/specworks/schema.yaml` (check artifacts, `validation`),
  `src/specworks/templates/validation.md`.
- `src/specworks/workflow/review.py` (findings of any check artifact),
  `cycle.py`, `checks.py`, `gate.py`, `validate.py`, `artifacts.py`.
- `src/specworks/cli/workflow.py` (`finding`, `cycle`, `validate --write`).
- Skills: `specworks-validate`, `specworks-review`, `specworks-build`,
  `specworks-reopen`, `_shared/back-from-review.md`; `tests/test_skills.py`
  (validate is no longer read-only).
- Existing `review.md` files, archived ones included, read the same.

## Out of Scope

- The inspect skill and `inspection.md` (`add-inspect-skill`, built on top of
  this change with a schema entry and a template).
- Validate warnings as findings (they stay in the output and the Summary).
- Moving existing findings between artifacts, or one findings file per change.
