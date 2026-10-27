# Proposal: add-expected-outcomes

## Why

A refinement goes from the problem straight to the options, so nothing
records what the user should observably see once the change is done, and
specify has nothing to check its requirements against. The refinement chose
Option A: add expected outcomes to the refinement, as text only.

## What Changes

- `src/specworks/templates/refinement.md`: a `## Outcomes` section between
  Problem and Context, a list of what a person outside the codebase would see
  or measure once the change is done (`None: <why>` when there is no visible
  outcome). Each option gets a line saying which outcomes it meets or fails.
- `src/specworks/schema.yaml`:
  - refinement instruction: an **Outcomes** bullet (observable results, not
    the solution; agreed before the options; alternatives offered with a
    recommendation when an outcome could go more than one way; `None: <why>`
    instead of an invented outcome); Options are weighed against the
    outcomes; Problem paraphrases or references its sources (an issue, a
    link, a doc) and names no individuals, instead of "Quote the user's
    words where they matter".
  - proposal instruction: What Changes is built from the chosen option and
    the outcomes; every outcome is covered by a requirement or listed under
    Out of Scope.
- `specworks-refine/SKILL.md` step 3: outcomes are agreed with the user
  after the problem and before the options; when an outcome could go more
  than one way, the agent offers the alternatives as numbered options with
  one recommended; options are compared against the outcomes.
- `specworks-specify/SKILL.md` step 2: the refinement's outcomes drive the
  proposal along with its recommended option and open questions; every
  outcome is covered by a requirement or listed under Out of Scope.
- `specworks-baseline/SKILL.md`:
  - step 3: each suspected bug notes the correct behaviour, or, when more
    than one is plausible, the alternatives with the one recommended;
  - step 4: the bug list shows those alternatives, so the user confirms one;
    the fix change's refinement gets `## Outcomes` = the behaviour the user
    confirmed (Options and Recommendation stay "Pending").
- `tests/test_skills.py`: wording checks for the template, the instructions
  and the three skills. Installed copies refreshed with `specworks skills`.
- Assumption: refinements already in `changes/active/` and the archive are
  left as they are; no code reads the Outcomes section.

## Capabilities

None: template, instruction and skill text only; the change is marked
`skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `src/specworks/templates/refinement.md`, `src/specworks/schema.yaml`, the
  refine, specify and baseline skills and their installed copies,
  `tests/test_skills.py`. No CLI change: `specworks instructions` returns the
  new text through the same keys.

## Out of Scope

- A check that enforces outcome coverage (`check` / `trace`): the
  refinement's Option B, left as an open question for later.
- Outcomes in `proposal.md` for changes that skip refinement.
- The other IntentSpec fields (edge cases, verification, evidence, status).
