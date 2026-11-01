# Refinement: share-skill-rules

## Problem

Several rules are written by hand in every skill that needs them, each copy
differing only in a phase name or one sentence: "Back from review" in
design, test and code; "if a gate fails, stop" and "the test command is not
configured" in test and code. When one copy changes the others drift (the
start skill's command list missed `config set` until a later change caught
it). The shared includes in `_shared/` cannot hold these rules today because
an include is copied verbatim, with no way to vary a word.

## Outcomes

- Each of these rules is written once, in `_shared/`; editing that file
  changes every skill that uses it at the next `specworks skills`.
- Each installed skill still reads with its own exact wording (e.g.
  `finding done R<n> --in test` in the test skill): no generic placeholder
  reaches the agent.

## Context

**Observed:**
- `src/specworks/tools/skills.py`: `INCLUDE_RE` matches
  `<!-- specworks:include <name> -->` and the include is filled in verbatim
  from `src/specworks/skills/_shared/<name>.md` when the skill is read.
- Six shared files today: running-cli (13 skills), asking-the-user (13),
  picking-the-change (9), committing (7), phase-subagents (2), pushing (2).
  No other paragraph is copied word for word between skills.
- Hand-repeated rules with small differences: "Back from review" in
  `specworks-design`, `specworks-test`, `specworks-code` (the `--in <phase>`
  value, the phases it lists, one sentence on who records a finding routed
  to both halves); the gate-fail stop and the missing test command in
  `specworks-test` and `specworks-code`.
- `tests/test_skills.py` checks some skill wording verbatim.
- Living docs: `src/specworks/tools/docs` (integrations).

**Assumed:**
- Agents follow a concrete `--in test` more reliably than a generic "the
  phase you are running".

## Constraints

- [hard] Includes without parameters behave exactly as today.
- [hard] A parameter left unfilled, or one the file does not use, fails at
  install time naming the skill and the key: never a half-filled skill.
- [hard] Files are read with `encoding="utf-8"`.
- [soft] The shared text reads the same in every skill except for its
  parameters.

## Options

### Option A: includes with parameters

`<!-- specworks:include <name> key=value key2="two words" -->`; the shared
file's `{key}` is replaced by the value when the skill is filled in.

- **Pros:** each rule written once; each skill keeps its exact wording.
- **Cons:** a small code change with its specs and tests.
- **Effort:** S
- **Touches:** integrations, skills
- **Outcomes:** meets both.

### Option B: one shared file per phase variant

`back-from-review-test.md`, `back-from-review-code.md`, ...

- **Pros:** no code change.
- **Cons:** the copies only move into `_shared/` and still drift.
- **Effort:** S
- **Touches:** skills
- **Outcomes:** meets the second only.

### Option C: one shared file per rule with a per-phase table

Included verbatim; each skill carries every phase's row.

- **Pros:** no code change; one file per rule.
- **Cons:** every skill carries rows for other phases; the agent picks its
  own.
- **Effort:** S
- **Touches:** skills
- **Outcomes:** meets the first; the second only partly.

## Recommendation

Option A, agreed with the user. In scope: parameters on includes, and moving
"Back from review" (design, test, code), the gate-fail stop and the missing
test command (test, code) into `_shared/` with parameters, each installed
skill keeping its current wording. Out of scope: "starting the phase" (the
gates differ in substance per phase), "re-read from disk" (one line),
specify's own back-from-review steps, and adopt/start's wording.

## Open Questions

- None blocking the proposal.

## Candidate Capabilities

- `integrations`: modified - filling in includes with parameters when the
  skills are installed.
