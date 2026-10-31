# Proposal: deterministic-steps

## Why

In 3 of the last 4 builds a `[code]` task's verification needed the test
half's tests, so the code half could not tick it and the build needed a
question and an extra run after the merge; in 2 merges, wording tests and
skill text did not match. The refinement chose Option B: text rules for both
halves, plus a warning in `specworks check` for the most expensive cause.

## What Changes

- `specworks check` warns, without failing, when a `[code]` task names the
  number of a `[test]` task of the same change, or requires the suite
  (`specworks run test`). The warning names both tasks, or the suite, and
  says how to verify instead. `gate specify` shows it, as it shows every
  `check` warning.
- `src/specworks/schema.yaml`:
  - tasks instruction: a `[code]` task is verified by lint, typecheck or
    observable behaviour, never by the test half's tests or by the suite;
    the suite runs in `gate implement` after the merge;
  - design instruction: a change whose tests check text (skill wording,
    templates, instructions) lists the exact phrases under
    **Pinned wording**, in `## Decisions`.
- `specworks-code/SKILL.md`: a `[code]` task is ticked when its own checks
  pass; the suite is not part of them.
- `specworks-test/SKILL.md`: wording checks assert only the pinned phrases,
  verbatim.
- `specworks-code/SKILL.md`: text the change writes uses the pinned phrases
  verbatim.
- `specworks-specify/SKILL.md` step 7: tasks follow the rule; fix every
  `check` warning about them before the gate.
- Installed copies refreshed with `specworks skills`.
- Assumption: a task number (`N.M`) in a `[code]` task's text that matches a
  `[test]` task of the change is a reference to it.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `specs`: new REQ-SPECS-015, the warning about a `[code]` task that depends
  on the test half.

## Impact

- `src/specworks/specs/check.py` (`_check_tasks`), `src/specworks/schema.yaml`,
  the code, test and specify skills and their installed copies,
  `tests/test_specs.py` (or the module holding the task checks) and
  `tests/test_skills.py`.

## Out of Scope

- Checking the pinned phrases (the refinement's Option C).
- The other manual steps in the refinement's sequence (review.md commands,
  `specworks commit`, `config set`, `capability add --create`, `new`
  without a branch, shared rule text).
- Rewriting the tasks of archived changes.
