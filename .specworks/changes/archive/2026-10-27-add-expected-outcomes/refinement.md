# Refinement: add-expected-outcomes

## Problem

A refinement goes straight from the problem to the options: nothing records
what the user should observably see once the change is done. Options are
compared without a target, and `/specworks-specify` has nothing to check its
requirements against, so an agreed result can be lost between refinement and
specs without anyone noticing. IntentSpec (intentspec.org, v1.2) makes
`outcomes` one of its two required fields next to the objective, for this
reason.

## Outcomes

- A refinement written with `/specworks-refine` has an `## Outcomes` section:
  what a person outside the codebase would see or measure once the change is
  done, agreed with the user before the options are compared. A change with
  no visible outcome says `None: <why>` instead of inventing one.
- Each option in a refinement is weighed against the outcomes (which ones it
  meets or fails).
- When an outcome could reasonably go more than one way, the agent offers the
  alternatives as numbered options with one marked (recommended), instead of
  choosing silently.
- `/specworks-baseline` lists, for each suspected bug, the correct behaviour;
  when more than one is plausible, the alternatives with a recommendation.
  The behaviour the user confirms is the `## Outcomes` of the bug's
  `fix-<name>` refinement.
- `/specworks-specify` covers every outcome of the refinement with a
  requirement, or lists it under Out of Scope, and builds What Changes from
  the chosen option and the outcomes.
- A refinement paraphrases or references its sources (an issue, a link, a
  doc) instead of quoting people, and names no individuals.

## Context

**Observed:**
- `src/specworks/templates/refinement.md`: Problem, Context, Constraints,
  Options, Recommendation, Open Questions, Candidate Capabilities; no outcomes.
- `src/specworks/schema.yaml`: the refinement instruction (Problem says
  "Quote the user's words where they matter") and the proposal instruction
  ("build on its chosen option").
- `src/specworks/skills/specworks-refine/SKILL.md` step 3 (Explore) lists what
  to make clear: problem, scope, constraints, options, preference.
- `src/specworks/skills/specworks-specify/SKILL.md` step 3: the refinement's
  "recommended option and open questions drive the proposal".
- `src/specworks/skills/specworks-baseline/SKILL.md` steps 3-4: each suspected
  bug notes "what was expected instead"; the fix change's refinement gets
  Problem and Context, with Options and Recommendation "Pending".
- REQ-FLOW-002 says instructions name their template and instruction, not
  their content; the only test on the template's content,
  `tests/test_cli.py:216`, checks for `## Options`.
- Skills have no capability (CLAUDE.md), and the installed copies are
  refreshed with `uv run specworks skills`.

**Assumed:**
- Refinements already in `changes/active/` stay valid without an Outcomes
  section: no code reads the section.

## Constraints

- [hard] No CLI behaviour change: the change is marked `skip-specs`.
- [hard] `tests/test_cli.py` and `tests/test_skills.py` keep passing.
- [hard] Skills are edited in `src/specworks/skills/` only, and the installed
  copies are refreshed and committed with them.
- [soft] A refinement stays at 1-2 pages: the Outcomes section is a short list.

## Options

### Option A: Text only (template, instructions, skills)

Add `## Outcomes` to the refinement template; add the rules to the
refinement and proposal instructions in `schema.yaml`; refine agrees outcomes
before options, specify maps them, baseline offers the bug's behaviours with
a recommendation; refresh the installed skills.

- **Pros:** meets every outcome; small; no code to test or maintain.
- **Cons:** nothing enforces the mapping in specify; it relies on the agent.
- **Effort:** S
- **Touches:** none (template, instructions and skill text)

### Option B: A plus an enforced check

`specworks check` / `trace` fails when an outcome is neither referenced by a
requirement nor under Out of Scope.

- **Pros:** an outcome cannot be dropped silently.
- **Cons:** the CLI parses free Markdown text; it fixes a format before it
  has been used; needs its own REQ and ACs.
- **Effort:** M
- **Touches:** `workflow`, `specs`

### Option C: Outcomes in the proposal instead

Add `## Outcomes` to `proposal.md`, which every change has.

- **Pros:** covers small changes that skip refinement.
- **Cons:** outcomes come after the option is chosen, so they cannot guide
  the choice (fails outcome 2); the baseline fix changes have no proposal yet.
- **Effort:** S
- **Touches:** none

## Recommendation

Option A, agreed with the user: it meets every outcome at the lowest cost,
and outcomes are tried on a few changes before anything enforces them.

## Open Questions

- Should an enforced outcome check (option B) follow once a few changes have
  used outcomes? Not blocking. (who can answer: maintainer)

## Candidate Capabilities

- None: the change touches the refinement template, the instructions and the
  skills, which have no capability; no behaviour of `workflow` changes.
