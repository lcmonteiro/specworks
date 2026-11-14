# Proposal: improve-test-phase

## Why

The test half writes one happy-path test per acceptance criterion: no ranking
by risk, no look for invalid inputs, limits or I/O failures, no rule that a
test is isolated and would really fail. Specify never asks for error or limit
scenarios, so the test half has none to test. (Option A of refinement.md.)

## What Changes

- `specworks-test`, step 4, gains four rules where each test is written:
  - **risk**: rank the criteria by risk first; a high-risk criterion gets
    more than one case, a trivial one a single test;
  - **negative**: per criterion, look for the invalid input, limit or I/O
    failure that applies; test it when the criterion describes it, otherwise
    write no untagged test and name it in the report as a missing scenario,
    suggesting `/specworks-specify`;
  - **quality**: each test isolated (no shared state, no order dependence)
    and meaningful: would it fail if the THEN broke?;
  - **integration**: a criterion spanning capabilities is tested through the
    higher capability's public interface, without mocking the lower ones.
- `specworks-test`, step 7: the report lists the missing scenarios.
- `specworks-specify`, step 4: every requirement that takes input, does I/O
  or holds state has at least one error or limit scenario, or says why not.
- `tests/test_skills.py` pins the new phrases; the installed copies
  (`.claude/skills/`) are refreshed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: skill text only (`specworks skip-specs`); the skills have no capability.

## Related requirements

- REQ-FLOW-012 left: build cycles route findings; the test half's rules do not change them.
- REQ-FLOW-013 left: validate's checks are unchanged.
- REQ-INTEG-006 left: installing the skills is unchanged; only their text changes.
- REQ-HARNESS-001 left: one peer per skill is unchanged.

## Impact

- `src/specworks/skills/specworks-test/SKILL.md`, `src/specworks/skills/specworks-specify/SKILL.md`
- `.claude/skills/` (installed copies, regenerated)
- `tests/test_skills.py`
- No CLI, API or data change.

## Out of Scope

- A coverage check (`commands.coverage`, coverage findings in review or validate).
- Mutation testing.
- A shared "never declare success without evidence" line in `_shared/`.
- Root cause rules in the test skill's step 5, and evidence in step 7's table.
- A "Principles" section at the top of the test skill (option B).
