# Review: architecture-docs

Base: `origin/main`

## Findings

- [x] R1 **quality** The structural-change rule speaks of one block diagram per change ("a block diagram of the capability's structure", "the change's block diagram replaces the living one"), but a cross-cutting change, itself a reason to write design.md, can touch several capabilities; close step 4 runs per capability and has no way to tell which block diagram belongs to which capability's living `design.md` (no IDs; skip-specs) (`src/specworks/schema.yaml:150`, `src/specworks/templates/design.md:29`, `src/specworks/skills/specworks-close/SKILL.md:83`)
  - **Proposal**: back to code: the design instruction and the template comment ask for one block diagram per capability whose structure changes, named after it (`diagrams/<capability>-blocks.d2`); close step 4 takes, for each capability, the change's block diagram of that capability; refresh the installed copies with `uv run specworks skills`
  - **Decision**: back to code: one block diagram per capability whose structure changes, named `diagrams/<capability>-blocks.d2` (design instruction and template comment); close step 4 takes each capability's own; refresh the installed copies (agreed with the user)
  - done in code: the design instruction (`schema.yaml`) and the template comment ask for one block diagram per capability whose structure changes, `diagrams/<capability>-blocks.d2`; close step 4 takes the change's block diagram of each capability (none for it, or "No structural change": the living one stays); baseline step 5 names its block diagram the same way so close finds it; installed copies refreshed
  - confirmed in review (cycle 2): `schema.yaml:150`, `templates/design.md:29`, close step 4 (`specworks-close/SKILL.md:83`) and baseline step 5 (`specworks-baseline/SKILL.md:175`) name `diagrams/<capability>-blocks.d2`; the installed copies are current (`uv run specworks skills` changes nothing); the suite passes (678 tests)
- [x] R2 **quality** Specify step 6 still restates the rule as it was before R1: a structural change "gets a block diagram" (one per change, not one per capability whose structure changes), and "Write each one as `diagrams/<name>.d2`" gives no name for the block diagram; a specify run that follows this text can name it anything, and close step 4 then finds no `diagrams/<capability>-blocks.d2` for the capability and keeps the old living diagram, so the new one is silently dropped (`src/specworks/skills/specworks-specify/SKILL.md:141`)
  - **Proposal**: back to code: specify step 6 says a structural change gets one block diagram per capability whose structure changes, `diagrams/<capability>-blocks.d2`, and other diagrams `diagrams/<name>.d2`; refresh the installed copies with `uv run specworks skills`
  - **Decision**: back to code: specify step 6 asks for one `diagrams/<capability>-blocks.d2` per capability whose structure changes, other diagrams stay `diagrams/<name>.d2`; refresh the installed copies (agreed with the user)
  - done in code: specify step 6 asks for one block diagram per capability whose structure changes, `diagrams/<capability>-blocks.d2` (close looks for that name), and any other diagram as `diagrams/<name>.d2`; installed copies refreshed
  - confirmed in review (cycle 3): specify step 6 (`specworks-specify/SKILL.md:141`) asks for one `diagrams/<capability>-blocks.d2` per capability whose structure changes and other diagrams as `diagrams/<name>.d2`, matching the design instruction, the template, close step 4 and baseline step 5; the installed copies are current (`uv run specworks skills` changes nothing); the suite passes (678 tests)

## Changed files without tags

- None: `specworks review` lists no untracedSource or untracedTests. The tagged files it lists (`src/specworks/core/config.py`, `src/specworks/core/config_file.py`, `tests/test_skills.py`) change only a docstring, a comment and wording checks of skill text; the change is `skip-specs`.

## Summary

The instruction, template, four skills and three comments match the proposal and design; no mention of `architecture.md` is left in the packaged skills, templates, schema or config, and the suite passes (678 tests). Cycle 1 found R1 (quality): the block-diagram rule did not say how a change across several capabilities keeps one diagram per capability; cycle 2's code step carried it out (one `diagrams/<capability>-blocks.d2` per capability, close takes each capability's own), confirmed here. Cycle 2 found R2 (quality): specify step 6 still paraphrased the old one-diagram rule with no name for the block diagram; cycle 3's code step carried it out, confirmed here. Cycle 3 found no new drift: no open finding is left.
