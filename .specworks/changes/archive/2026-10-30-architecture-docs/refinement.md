# Refinement: architecture-docs

## Problem

Architecture is meant to be a living doc that agents read before deciding,
but no step of the flow produces it reliably. `architecture.md` is written
only when close judges that a change "altered structure", and since that is
rarely obvious from one change, no project gets one: this repository has none
in any of its 5 capabilities after about 40 changes. Block diagrams are
allowed in a change's design but are optional, and none has been drawn, so
agents decide about structure with no picture of it. (Source: user question
in session, paraphrased.)

## Outcomes

- When a change adds, removes or moves components, or changes the
  dependencies between them, its `design.md` has a block diagram; when it
  does not, its `## Diagrams` says "No structural change", so the decision
  is visible.
- Close carries that block diagram into the capability's living `design.md`
  (and its `docs/diagrams/`), replacing the one already there, so the living
  diagram shows the capability as it is now.
- Baseline gives a capability with more than one component a block diagram
  in its first living `design.md`.
- `architecture.md` is no longer mentioned: no skill, instruction or config
  comment points an agent to a file that never exists.

## Context

**Observed:**
- `src/specworks/skills/specworks-close/SKILL.md` step 4: `design.md` always,
  `architecture.md` "only when the change altered structure", diagrams
  copied to `<docsPath>/diagrams/` and rendered with `specworks diagrams
  --dir`.
- `src/specworks/schema.yaml` design instruction (`id: design`): diagrams
  are optional, "only where a picture explains what text cannot", a
  component diagram among the kinds; D2 rules (no colours or styles, one idea
  per diagram, about 12 shapes).
- `src/specworks/skills/specworks-refine/SKILL.md` lists `architecture.md`
  among the living docs to read; design and specify read only the living
  specs.
- `src/specworks/skills/specworks-baseline/SKILL.md` writes a short
  `design.md`, with no diagram; adopt writes no living docs.
- `architecture.md` is also named in comments: `core/config.py:42`,
  `core/config_file.py:25` (the default config's comment) and this
  repository's `.specworks/config.yml`.
- Diagrams render through pyd2's pinned d2 (REQ-INTEG-003) with
  `specworks diagrams`, in the workspace theme.

**Assumed:**
- Agents follow a written rule with an explicit "No structural change"
  escape more reliably than an optional one. Not measured.

## Constraints

- [hard] Block diagrams are D2 sources rendered through pyd2 with
  `specworks diagrams`, with no colours or styles (the theme gives the look).
- [hard] The rule works for any language: specworks projects are not only
  Python.
- [hard] No CLI behaviour change: the change is marked `skip-specs`.
- [soft] "When necessary" stays a judgement, but the judgement is written
  down.

## Options

### Option A: Rules in the instructions and skills

The design instruction requires a block diagram for a structural change, or
the line "No structural change" under `## Diagrams`. Close carries the
diagram into the living `design.md` and replaces the old one. Baseline draws
one for a capability with more than one component. Every mention of
`architecture.md` goes.

- **Pros:** small; any language; nothing new to maintain in the CLI.
- **Cons:** nothing checks that design followed the rule.
- **Effort:** S
- **Touches:** none (instructions, skill text and comments)
- **Outcomes:** meets all four; outcome 1 relies on the agent.

### Option B: A plus a gate warning

`gate design` and validate warn when `design.md` has neither an embedded
diagram nor "No structural change".

- **Pros:** outcome 1 is checked.
- **Cons:** a behaviour change in `workflow` with its own requirement; fixes
  the wording before it has been used.
- **Effort:** M
- **Touches:** `workflow`
- **Outcomes:** meets all four.

### Option C: Generate the diagram from the code

The CLI reads imports and dependencies and writes the `.d2` itself.

- **Pros:** always current.
- **Cons:** only for languages it can parse; shows imports, not the
  components a person would name.
- **Effort:** L
- **Touches:** `integrations`, `workflow`
- **Outcomes:** meets 1-3 only for the languages it parses; fails the
  any-language constraint.

## Recommendation

Option A, agreed with the user: the smallest change, and the rule is tried
on a few changes before anything enforces it.

## Open Questions

- Should the gate warning (option B) follow once a few changes have used the
  rule? Not blocking. (who can answer: maintainer)
- A project-wide picture of how the capabilities fit together is out of
  scope; it can be its own change. Not blocking. (who can answer: maintainer)

## Candidate Capabilities

- None: instructions, skill text and comments only; no behaviour of
  `workflow` changes.
