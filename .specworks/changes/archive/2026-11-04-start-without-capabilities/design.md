# Design: start-without-capabilities

## Context

Skill text, templates and README only; see proposal.md. The skill tests in
`tests/test_skills.py` check wording verbatim (`raw_skill_file` folds line
wraps into spaces), so the test and code halves share the phrases below.
`/specworks-start` today proposes capabilities in step 4 and registers them
in step 5 with `capability add --create`, which writes each `.gitkeep`.

## Goals / Non-Goals

**Goals:**
- Start creates the minimal tree with no capabilities.
- Capabilities are first proposed in a change's refinement, with module,
  code path and description, and registered at close (unchanged).
- Onboard routes a started project with no capabilities to refine.

**Non-Goals:**
- Any CLI change; `capability add --create` (REQ-CLI-014) stays.
- Changing adopt, specify or close.

## Decisions

### The start skill writes the two `.gitkeep` files

With no capability, no CLI command creates `src/` or `tests/`, and git does
not keep empty folders. The skill writes `src/.gitkeep` and
`tests/.gitkeep` (per module) with its Write tool. Alternatives: no folders
until the first change (the approved tree would not exist), or a CLI command
(refinement Option B, rejected as too much surface). The old tests that
require `capability add --create` and forbid a hand-written `.gitkeep` are
removed.

### The first architecture has no capabilities yet

`## Capabilities and how they interact` says none exist yet, and no block
diagram is written until the first capability is registered (close keeps
it current from then on). Start no longer runs `specworks diagrams --dir`.

### Onboard keys the empty-capabilities rows on `changes` and the config

Two rows replace "`capabilities` is empty", both only when `changes` is
empty (work in flight goes by its phase, further down the table):
a fresh config goes to start or adopt; a config with `context` or
`commands` set (start or adopt has run) goes to refine when there is no
code, adopt when there is.

### Pinned wording

The test half asserts these and the code half writes them, verbatim
(after folding line wraps):

`src/specworks/skills/specworks-start/SKILL.md`:
- S1: ``the minimal tree: `.specworks/`, `docs/`, `src/` and `tests/` ``
- S2: `No capabilities: the first change proposes them in its refinement, and close registers them.`
- S3 (in step 5, "Create it"): ``write an empty `src/.gitkeep` and `tests/.gitkeep` ``
- S4: the text never contains `specworks capability add` nor `capability add --create`.
- S5 (architecture, step 5): `` `## Capabilities and how they interact` says `None yet: the first change proposes them.` ``
- S6 (guardrails): `No capabilities: start never registers one.`

`src/specworks/skills/specworks-onboard/SKILL.md` (state table):
- O1: `` | `capabilities` and `changes` are empty, and so are `context` and `commands` | set up, nothing mapped | ``
- O2: `` | `capabilities` and `changes` are empty, and `context` or `commands` is set | started, no capability yet | ``
- O3: row O2's next step contains `` `/specworks-refine <first change>` when the repository has no code ``
- O4: the old row `` | `capabilities` is empty | `` is gone.

`src/specworks/schema.yaml` (refinement instruction) and
`src/specworks/templates/refinement.md`:
- R1 (instruction): `for a new capability say which module should own it, its code path and a one-line description`
- R2 (template): ``- `<!-- capability -->`: new (<!-- owning module -->, `<!-- code path -->`) | modified - <!-- what it covers, or why it changes -->``

`src/specworks/skills/specworks-refine/SKILL.md` (guardrails):
- F1: `say which module should own each one, its code path and a one-line description`

## Interfaces

None: no API changes; only skill, template and instruction text.

## Diagrams

No structural change.

## Risks / Trade-offs

- [the skill writes files by hand again] -> only the two fixed `.gitkeep`
  paths per module, pinned by S3.
- [a project started before this change has capabilities] -> unaffected:
  onboard's other rows still apply.
