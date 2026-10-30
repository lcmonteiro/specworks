# Review: architecture-docs

Base: `origin/main`

## Findings

- [ ] R1 **quality** The structural-change rule speaks of one block diagram per change ("a block diagram of the capability's structure", "the change's block diagram replaces the living one"), but a cross-cutting change, itself a reason to write design.md, can touch several capabilities; close step 4 runs per capability and has no way to tell which block diagram belongs to which capability's living `design.md` (no IDs; skip-specs) (`src/specworks/schema.yaml:150`, `src/specworks/templates/design.md:29`, `src/specworks/skills/specworks-close/SKILL.md:83`)
  - **Proposal**: back to code: the design instruction and the template comment ask for one block diagram per capability whose structure changes, named after it (`diagrams/<capability>-blocks.d2`); close step 4 takes, for each capability, the change's block diagram of that capability; refresh the installed copies with `uv run specworks skills`

## Changed files without tags

- None: `specworks review` lists no untracedSource or untracedTests. The tagged files it lists (`src/specworks/core/config.py`, `src/specworks/core/config_file.py`, `tests/test_skills.py`) change only a docstring, a comment and wording checks of skill text; the change is `skip-specs`.

## Summary

The instruction, template, four skills and three comments match the proposal and design; no mention of `architecture.md` is left in the packaged skills, templates, schema or config, and the suite passes (678 tests). One quality finding (R1): the block-diagram rule does not say how a change across several capabilities keeps one diagram per capability; proposed back to code.
