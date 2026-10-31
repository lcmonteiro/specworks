# Refinement: deterministic-steps

## Problem

The two halves of implement run in parallel and never see each other's work,
but the tasks and texts they work from often assume they do. In 3 of the last
4 builds, a `[code]` task's verification needed the test half's tests ("verify
the 1.1 checks pass", or `specworks run test` while the test half was changing
existing tests), so the code half could not tick it, `gate code` failed, and
the build needed a question to the user and an extra code-half run after the
merge. In 2 merges of one build, wording tests and skill text did not match
because each half picked its own phrases from the proposal, which cost a
question, a new task and two subagent runs each time. The user wants the
process as safe, deterministic and fast as possible. (Source: user request in
session, paraphrased; the builds of `dedupe-copilot-skills`,
`architecture-docs` and `add-start-skill`.)

## Outcomes

- In a build, the code half ticks every `[code]` task in its own run: no
  question and no second code-half run after the merge.
- No `[code]` task written by specify makes its verification depend on the
  test half's tests; it is verified by lint, typecheck or observable
  behaviour, and the full suite belongs to `gate implement` after the merge.
  `specworks check` warns when a `[code]` task does otherwise.
- In a change whose tests check text (skill wording, templates,
  instructions), `design.md` lists the exact phrases; the test half checks
  only those, the code half writes them as they are, and no merge needs a
  wording-test fix.

## Context

**Observed:**
- `src/specworks/schema.yaml`, tasks instruction: "Every task says how to
  verify it"; nothing forbids a `[code]` task naming a `[test]` task or the
  suite. Recent `tasks.md` files did both.
- `gate code` (REQ-FLOW-007/008): every `[code]` task done is blocking; the
  suite is only a warning when the change has its own test files. So an
  unticked task, not the suite, is what blocks.
- `src/specworks/specs/check.py` `_check_tasks`: already warns about a
  missing `[test]` or `[code]` task (REQ-SPECS-009); `specworks check` runs
  in specify, before the build.
- The design instruction has no place for agreed phrases; the test skill
  writes checks from the proposal, the code skill writes text from it.
- Other manual steps found (sequence below): review.md lines, commits, config
  edits, `.gitkeep` folders, `new` switching branch, one rule in 5 places.

**Assumed:**
- A task ID like `1.1` in a `[code]` task's text always means a reference to
  that task; false positives (a version number) are rare enough for a
  warning.

## Constraints

- [hard] The halves stay independent: the code half never reads the test
  half's tests.
- [hard] The suite is still required: `gate implement` after the merge, and
  validate.
- [hard] The check is a warning, never an error, and works on the task text
  alone.
- [soft] The warning does not fire on ordinary wording.

## Options

### Option A: Text rules only

The tasks instruction says how a `[code]` task is verified; the code skill
ticks a task when those checks pass; the design instruction gets a "Pinned
wording" section; the test and code skills use it verbatim.

- **Pros:** small; no code.
- **Cons:** nothing stops a dependent task from coming back.
- **Effort:** S
- **Touches:** none (instructions and skills)
- **Outcomes:** meets 1-3, but outcome 2 relies on the agent.

### Option B: A plus a warning in `specworks check`

`check` warns when a `[code]` task names the ID of a `[test]` task of the
same change, or requires the suite (`specworks run test`).

- **Pros:** outcome 2 is checked, in specify, where a fix is cheapest.
- **Cons:** a behaviour change in `specs` with its own requirement.
- **Effort:** M
- **Touches:** `specs`
- **Outcomes:** meets all three; outcome 2 is deterministic.

### Option C: B plus a check of the pinned phrases

`check` or `gate test` confirms each pinned phrase appears in the tests and
in the changed text.

- **Pros:** outcome 3 is deterministic too.
- **Cons:** a fixed format for the section and another rule to keep.
- **Effort:** M-L
- **Touches:** `specs`, `workflow`
- **Outcomes:** meets all three, deterministically.

## Recommendation

Option B, agreed with the user: it makes the most expensive cause
deterministic with a small, testable warning; the pinned phrases stay a rule.

## Open Questions

- Sequence for later changes, each its own change, in this order: commands
  for review.md lines (`specworks finding decide/done`; `review` is already a
  command); `specworks commit --change`; `specworks config set`;
  `capability add --create`; a config option so `new` does not switch
  branch; shared text for rules repeated across skills. Not blocking.
  (who can answer: maintainer)
- Should Option C follow if pinned phrases still drift? Not blocking.
  (who can answer: maintainer)

## Candidate Capabilities

- `specs`: modified - `check` warns about `[code]` tasks that depend on the
  test half (REQ-SPECS-009 or a new requirement)
