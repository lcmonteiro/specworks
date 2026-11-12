# Refinement: unify-check-findings

## Problem

Only the review step leaves findings the flow can follow: `review.md` holds
`R<n>` findings that route the change back to a phase, the phases mark them
done and review closes them. Validate leaves nothing: a FAIL lives only in the
conversation, and the phase the change goes back to gets no input. The
upcoming inspect step (`add-inspect-skill`, refined, depends on this change)
has no format to write its notes in. The three check steps (review, validate,
inspect) should work the same way: each writes its own artifact with findings
in one format, decides where the change goes, and that artifact is the input
of the next step.

## Outcomes

- Review, validate and inspect each write their own artifact (`review.md`,
  `validation.md`, `inspection.md`) with findings in one format (`R<n>`,
  `V<n>`, `I<n>`: type, location, `back to <phase>`).
- The phases read the open findings routed to them from every check artifact
  and mark them done; the step that found a finding confirms and closes it
  (review its R, validate its V on its next run, inspect its I).
- A validate FAIL leaves its V findings in `validation.md`: the CLI writes one
  per failed critical check (`specworks validate --write`), the skill adds the
  ones from its own reading.
- The next state of a change is computed from the open findings of all check
  artifacts (the earliest phase any of them asks for, else the next step of
  the flow), and `back to review` is a valid route.
- The review gate blocks on open R findings, the validate gate on open R and V
  findings; I findings never block.

## Context

**Observed:**
- `workflow/review.py` parses `review.md`: `- [ ] R<n> **<type>** ...`, types
  mapped to a phase (`spec-gap` → specify, `design-gap` → design, `test-gap` →
  test, `code-gap`/`tag`/`quality` → code), `back to <specify|design|
  implement|test|code>:` and `back to design only:` routes, `done in <step>:`
  (REQ-FLOW-010). `back to review` is not a route.
- `workflow/cycle.py` (`specworks cycle`, REQ-FLOW-012) reads only `review.md`
  to compute the next cycle (`startAt`, `phases`).
- `workflow/checks.py`: `review_written`, `review_readable`, `review_closed`
  are used by the review gate (REQ-FLOW-011) and by validate.
- `workflow/validate.py` (REQ-FLOW-013) runs grouped checks, each with the
  phase skill that fixes it (`fix`), and returns `verdict` and `goBackTo`; it
  writes nothing. `/specworks-validate` is read-only and does not commit
  (`tests/test_skills.py::test_validate_is_read_only_and_does_not_commit`).
- `specworks finding add|decide|done|close` (cli, REQ-CLI-011) write only
  `review.md`. `/specworks-reopen` adds an R finding when it reopens at review.
- The phases read findings through the shared skill text `back-from-review`
  and `specworks cycle`; build runs the cycle from them.
- Artifacts are declared in `src/specworks/schema.yaml`, templates in
  `src/specworks/templates/`.

**Assumed:**
- Validate's checks map to finding types through their `fix` phase
  (specify → spec-gap, ..., review → a route back to review).
- Rerunning validate can tell which of its own V findings now pass, so it can
  close them.

## Constraints

- [hard] Existing `review.md` files, archived ones included, stay valid and
  read the same.
- [hard] Errors stay values (`{"error": ...}` with exit 1 under `--json`),
  paths relative to the workspace root.
- [hard] One change at a time: `add-inspect-skill` is built after this one
  closes and only adds its artifact on top.
- [soft] Validate stops being read-only: it writes its own artifact and
  commits it.

## Options

### Option A: Check artifacts declared in the schema

Each check artifact declares its findings in `schema.yaml`
(`findings: {prefix: V, gate: validate}`). `review.py` becomes a generic
findings module; the parser, `specworks cycle`, the gates and
`specworks finding ... --in <artifact>` go through the declared ones.

- **Pros:** one model; "each check step has its own artifact" is explicit;
  inspect is added with a schema entry and a template.
- **Cons:** a new concept in the schema.
- **Effort:** M
- **Touches:** workflow, cli, templates, skills (validate, review, build,
  reopen, `_shared/back-from-review`)
- **Outcomes:** meets all five.

### Option B: Two files known by name

The parser takes the ID prefix; cycle, the gates and `finding` know
`review.md` and `validation.md` by name.

- **Pros:** a smaller, direct diff now.
- **Cons:** every new check step touches the parser, the gates, cycle and
  `finding` again; inspect would.
- **Effort:** S/M
- **Touches:** workflow, cli, templates, the same skills
- **Outcomes:** meets all five, at a cost for every later check step.

## Recommendation

Option A, agreed with the user: inspect, which comes next, then needs no
change to the parser, the gates or cycle.

## Open Questions

- Do validate's WARNINGs become non-blocking V findings, or stay only in the
  summary? (who can answer: the user, at specify)
- Does a PASS write `validation.md` with "None."? (who can answer: the user,
  at specify)

## Candidate Capabilities

- `workflow`: modified - findings in every declared check artifact, the next
  cycle and next state from all of them, per-step gates, `back to review`,
  validate writing `validation.md`.
- `cli`: modified - `specworks finding ... --in <artifact>`,
  `specworks validate --write`.
- The skills validate, review, build, reopen and `_shared/back-from-review`
  change their wording (skills have no capability yet).
