# Proposal: architecture-docs

## Why

No step of the flow produces architecture reliably: `architecture.md` is
written only when close judges a change "altered structure", so no project
has one, and block diagrams in a design are optional and never drawn. The
refinement chose Option A: the capability's living `design.md` carries a
block diagram when its structure needs one, by rules in the instructions and
skills, and `architecture.md` goes.

## What Changes

- `src/specworks/schema.yaml`, design instruction:
  - a change that adds, removes or moves components, or changes the
    dependencies between them, is a reason to write `design.md`;
  - **Diagrams**: such a change gets a block diagram (components as nested
    containers, connections labelled with what flows); otherwise the section
    says "No structural change". The other kinds stay optional.
- `src/specworks/templates/design.md`: the `## Diagrams` comment says the
  same (a block diagram for a structural change, else "No structural
  change").
- `specworks-specify/SKILL.md` step 6: diagrams follow that rule rather than
  "when they help".
- `specworks-close/SKILL.md` step 4: the `architecture.md` bullet goes;
  `design.md` keeps one block diagram of the capability as it is now: the
  change's block diagram replaces the living one in `<docsPath>/diagrams/`
  and is embedded in the living `design.md`.
- `specworks-baseline/SKILL.md` step 5: for a capability with more than one
  component, the baseline's `design.md` also has a block diagram of the
  existing structure (so close puts it in the first living `design.md`).
- `specworks-refine/SKILL.md` step 1: the living docs listed are `spec.md`,
  `requirements.md` and `design.md` (with its diagrams).
- Comments: `core/config.py:42`, the default config written by
  `core/config_file.py:25`, and this repository's `.specworks/config.yml`
  name the living docs without `architecture.md`.
- `tests/test_skills.py`: wording checks for the instruction, the template
  and the three skills. Installed copies refreshed with `specworks skills`.
- Assumption: "more than one component" is the agent's reading of the code;
  no count is checked.

## Capabilities

None: instructions, templates, skill text and comments only; the change is
marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- `src/specworks/schema.yaml`, `src/specworks/templates/design.md`, the
  specify, close, baseline and refine skills and their installed copies,
  comments in `src/specworks/core/config.py` and `config_file.py`,
  `.specworks/config.yml`, `tests/test_skills.py`. No CLI change:
  `specworks instructions` returns the new text through the same keys.

## Out of Scope

- A warning in `gate design` or validate (the refinement's Option B).
- A project-wide picture of how the capabilities fit together.
- Drawing block diagrams for this repository's existing capabilities: each
  gets one at its next structural change.
