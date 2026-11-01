# Review: specify-related-requirements

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **code-gap** AC-SPECS-016.6 says a blank term is refused naming the term; find_requirements raises ConfigError("empty search term") without it (src/specworks/specs/capabilities.py:244), and the test only checks that phrase (tests/test_find_requirements.py:207), so it would pass either way (REQ-SPECS-016)
  - **Proposal**: back to implement: raise ConfigError(f"empty search term: {term!r}") for the first blank term (still containing the pinned 'empty search term'); the test asserts the repr for each parametrized case ("''", "' '")
  - **Decision**: back to implement: raise ConfigError(f"empty search term: {term!r}") for the first blank term, and the AC-SPECS-016.6 test asserts the repr in each case

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

None: `specworks review` lists no untraced source or test file. The changed
files it lists as other (`src/specworks/skills/specworks-specify/SKILL.md` and
its installed copy `.claude/skills/specworks-specify/SKILL.md`,
`src/specworks/schema.yaml`, `src/specworks/templates/proposal.md`) are skill,
instruction and template text with no capability, checked by the wording tests
in `tests/test_skills.py` as design.md decides.

## Summary

<!-- Two or three lines: what was found, what changed in code, specs and design, and anything sent back to an earlier phase. -->

The suite passes (862 tests) and lint and typecheck are clean; the code matches
design.md's Interfaces and Decisions, and `spec find "config set"` lists
REQ-CLI-013 in this repository. One finding: R1 (code-gap), the blank-term
error does not name the term as AC-SPECS-016.6 says, proposed back to
implement (code and its test). Nothing was changed in code, specs or design.
Note for a future change: the header line counts as the title, so a term such
as `requirement` or an ID prefix matches every requirement.
