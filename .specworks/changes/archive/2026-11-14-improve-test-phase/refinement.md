# Refinement: improve-test-phase

## Problem

The test half (`/specworks-test`) writes at least one test per acceptance
criterion and stops there: in practice one happy-path test, with no ranking
by risk, no look for invalid inputs, limits or I/O failures, and no rule for
whether a test is isolated and would really fail. Upstream, `/specworks-specify`
never asks for error or limit scenarios, so the test half has none to test.
A set of testing-engineer principles (understand, unit/integration,
negative, regression, risk-based, coverage, quality, root cause, evidence)
was compared with the skills; most are already covered, these gaps are not.

## Outcomes

- The test half's tests give high-risk criteria (data loss, security,
  user-visible errors, behaviour many callers rely on) more than one case,
  and trivial ones a single test.
- A criterion with no error or limit scenario where one applies is named in
  the test half's final report as a missing scenario, with `/specworks-specify`
  suggested, instead of getting an untagged test.
- New specs carry an error or limit scenario for each requirement with
  inputs, I/O or state, or say why there is none.

## Context

**Observed:**
- `src/specworks/skills/specworks-test/SKILL.md`, step 4: "at least one
  test that checks exactly what its WHEN/THEN says", "Cover error scenarios
  with the real error type", "Pick the level the criterion needs", "Keep
  tests deterministic". Guardrail: "Tests verify the acceptance criteria as
  written", so untagged extra tests go against the flow.
- Steps 2-3 already cover *understand*; step 5 and the MODIFIED/REMOVED rules
  cover *regression*; "never weaken an assertion, skip a test" covers
  *evidence*; "fail for the right reason" covers *root cause*.
- `src/specworks/skills/specworks-specify/SKILL.md` has no rule on error or
  limit scenarios.
- `specworks-review` already checks "would it fail if the behaviour broke"
  and "errors, limits and edge cases in the scenarios", but only after both
  halves are written.
- `tests/test_skills.py` pins skill wording verbatim; skills are edited in
  `src/specworks/skills/` and refreshed with `uv run specworks skills`.
- Coverage is measured only by CI (`[tool.coverage.report] fail_under`); no
  phase runs it, and the test half runs against stubs, so it cannot.

**Assumed:**
- Agents follow concrete rules inside a step better than a principles list.

## Constraints

- [hard] Skill text only: no CLI behaviour, so the change is `specworks skip-specs`.
- [hard] No untagged tests: every test still traces to a criterion (`@ac`).
- [hard] Skills are edited in `src/specworks/skills/`, installed copies
  refreshed and committed together; pinned phrases get wording tests.
- [soft] Keep the test skill short: one bullet per rule in step 4.

## Options

### Option A: Inline rules in step 4

Add four bullets to step 4 of the test skill (risk, negative, quality,
integration) and one rule to specify's scenario writing.

- **Pros:** the rules sit where each test is written; no repetition.
- **Cons:** no single list of principles to read at a glance.
- **Effort:** S
- **Touches:** none (skills)
- **Outcomes:** meets all three.

### Option B: A "Principles" section at the top

A short list of testing principles at the top of the test skill; step 4
unchanged.

- **Pros:** the stance is visible at once.
- **Cons:** abstract; agents may read it and not apply it per test.
- **Effort:** S
- **Touches:** none (skills)
- **Outcomes:** meets them only if the agent applies the principles unprompted.

### Option C: Both

Short principles at the top, the concrete rules in step 4.

- **Pros:** stance and steps.
- **Cons:** says each thing twice; the skill grows.
- **Effort:** S
- **Touches:** none (skills)
- **Outcomes:** meets all three.

## Recommendation

Option A, agreed with the user. In scope:
1. Test skill, step 4, **risk**: rank criteria by risk; high-risk ones get
   more cases (limits, invalid inputs), trivial ones one test.
2. Test skill, step 4, **negative**: per criterion, ask which invalid input,
   limit or I/O failure applies; test it when the criterion describes it,
   otherwise name it as a missing scenario in the final report and suggest
   `/specworks-specify` (no untagged test).
3. Test skill, step 4, **quality**: each test isolated (no shared state or
   order dependence) and meaningful: "would it fail if the THEN broke?",
   else strengthen it.
4. Test skill, step 4, **integration**: a criterion spanning capabilities is
   tested through the higher capability's public interface, without mocking
   the lower ones.
5. Specify skill: every requirement with inputs, I/O or state gets at least
   one error or limit scenario, or says why it has none.
6. Wording tests in `tests/test_skills.py` for the pinned phrases of 1, 2, 3, 5.

Out of scope (decided with the user): a coverage check (`commands.coverage`,
coverage findings in review/validate), mutation testing, a shared "never
declare success without evidence" line, root cause in step 5, and evidence
in step 7's table.

## Open Questions

- None blocking.

## Candidate Capabilities

- None: skill text only (`specworks skip-specs`); the skills have no capability.
