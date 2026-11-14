# Design: improve-test-phase

## Context

See proposal.md. Skill text only: two `SKILL.md` files under
`src/specworks/skills/`, their installed copies, and wording tests in
`tests/test_skills.py`, which reads the packaged skill with `read_skill`
and flattens whitespace.

## Goals / Non-Goals

- Goal: the four test rules sit in step 4 of `specworks-test`, where each
  test is written; specify asks for error or limit scenarios.
- Non-goal: any CLI check of these rules (gates, `check`, `validate`).

## Decisions

### Rules inline, in step 4 of the test skill

Option A of refinement.md: one rule per bullet, in the step where tests are
written. Alternatives: a "Principles" section at the top (abstract, applied
less), or both (says everything twice); rejected with the user.

- **Risk** opens step 4, before the per-criterion bullets, since it decides
  how many cases each criterion gets:
  > Rank the criteria by risk first: data loss, security, user-visible
  > errors and behaviour many callers rely on are high risk. A high-risk
  > criterion gets more than one case (its limits, invalid inputs and
  > failures); a trivial one gets a single test.
- **Negative** is a new bullet after "Write at least one test":
  > Look for the negative cases: for each criterion, ask which invalid
  > input, limit or I/O failure applies. Test it when the criterion
  > describes it. When it does not, write no untagged test: name it in the
  > report as a missing scenario and suggest `/specworks-specify <ref>`.
- **Integration** extends the "Pick the level" bullet:
  > A criterion that spans capabilities is tested through the public
  > interface of the higher one, without mocking the lower ones.
- **Quality** replaces the "Keep tests deterministic" bullet:
  > Keep each test isolated, deterministic and meaningful: no shared
  > state and no dependence on the order tests run in; control time,
  > randomness, network and filesystem the way the project already does.
  > Ask of every test: would it fail if the THEN broke? If not, strengthen it.
- Step 7's report adds the missing scenarios to what it lists.

The guardrail "Tests verify the acceptance criteria as written" stays: a
missing scenario goes back to specify, never into an untagged test.

### Error or limit scenarios in specify

Step 4 of `specworks-specify`, after the SHALL/MUST and scenario rule:
> Every requirement that takes input, does I/O or holds state has at least
> one error or limit scenario; when it has none, the requirement says why.

### Pinned wording

- `Rank the criteria by risk first` (test skill)
- `write no untagged test: name it in the report as a missing scenario` (test skill)
- `would it fail if the THEN broke?` (test skill)
- `at least one error or limit scenario` (specify skill)

The existing pinned phrases of both skills stay verbatim.

## Interfaces

None: no public API, data shape or CLI surface changes.

## Diagrams

No structural change.

## Risks / Trade-offs

- [risk] Step 4 grows and agents skim it -> one short bullet per rule, no
  examples beyond the existing ones.
- [risk] "Say why" in specify adds prose to every pure-logic requirement ->
  only requirements with input, I/O or state need a scenario at all.

## Open Questions

None.
