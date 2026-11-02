# Review: specify-related-requirements

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **code-gap** AC-SPECS-016.6 says a blank term is refused naming the term; find_requirements raises ConfigError("empty search term") without it (src/specworks/specs/capabilities.py:244), and the test only checks that phrase (tests/test_find_requirements.py:207), so it would pass either way (REQ-SPECS-016)
  - **Proposal**: back to implement: raise ConfigError(f"empty search term: {term!r}") for the first blank term (still containing the pinned 'empty search term'); the test asserts the repr for each parametrized case ("''", "' '")
  - **Decision**: back to implement: raise ConfigError(f"empty search term: {term!r}") for the first blank term, and the AC-SPECS-016.6 test asserts the repr in each case
  - done in implement: find_requirements raises ConfigError(f"empty search term: {term!r}") for the first blank term (src/specworks/specs/capabilities.py)
  - confirmed in review: find_requirements raises ConfigError(f"empty search term: {term!r}") for the first blank term (src/specworks/specs/capabilities.py:243-245); the AC-SPECS-016.6 test asserts the exact message with the repr for '', ' ' and a blank second term (tests/test_find_requirements.py:203-207); spec find --json ' ' prints {"error": "empty search term: ' '"} and exits 1
- [ ] R2 **design-gap** design.md still gives the blank-term error as ConfigError("empty search term") (Decisions > Matching, and Interfaces > find_requirements), while the code, as R1 agreed, raises ConfigError(f"empty search term: {term!r}") for the first blank term (src/specworks/specs/capabilities.py:245) (REQ-SPECS-016)
  - **Proposal**: back to design: in design.md, Matching and the find_requirements interface say it raises ConfigError(f"empty search term: {term!r}") for the first blank term; the pinned message 'empty search term' stays; no code or test change
  - **Decision**: back to design: update Decisions > Matching and Interfaces > find_requirements in design.md to ConfigError(f"empty search term: {term!r}"); no code or test change

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

Cycle 1: the suite passed (862 tests), lint and typecheck were clean, and
`spec find "config set"` lists REQ-CLI-013 in this repository. One finding:
R1 (code-gap), the blank-term error did not name the term, sent back to
implement. Cycle 2: R1 is done and confirmed (the suite passes, 862 tests).
One new finding: R2 (design-gap), design.md still gives the old message,
proposed back to design (text only, no code or test change). Nothing was
changed in code, specs or design in review.
Note for a future change: the header line counts as the title, so a term such
as `requirement` or an ID prefix matches every requirement.
