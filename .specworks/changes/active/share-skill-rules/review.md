# Review: share-skill-rules

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **spec-gap** update_skills now fills in every skill before removing stale ones, so `specworks update` with a failing include changes nothing on disk (design.md, Filling in), but REQ-INTEG-007 and AC-INTEG-007.6 name only `specworks skills`, and no test fails if update_skills goes back to removing first (src/specworks/tools/skills.py:329)
  - **Proposal**: back to specify: name `specworks update` next to `specworks skills` in REQ-INTEG-007 and add AC-INTEG-007.8 (a packaged include fails, `specworks update` exits 1, no skill folder removed or changed), with its [test] task; the code already does it
- [ ] R2 **quality** start-implement.md relies on having no trailing newline: the code skill keeps a blank line after the include and the test skill a line starting with a space (' Tests built on an undecided API...') to rebuild the original text; an editor or end-of-file fixer adding the newline silently changes both installed skills, and no test checks the repo's installed copies (src/specworks/skills/_shared/start-implement.md:10, src/specworks/skills/specworks-test/SKILL.md:48-49, src/specworks/skills/specworks-code/SKILL.md:38-39)
  - **Proposal**: back to design: give start-implement.md a `{{note}}` after 'themselves fail).' and a trailing newline, as back-from-review.md does; the test skill passes note=" Tests built on an undecided API test the wrong thing.", the code skill note="", and both drop the extra line; installed copies stay byte for byte the same

## Changed files without tags

None: `specworks review` lists no untracedSource or untracedTests. The skill
files (`src/specworks/skills/_shared/back-from-review.md`,
`src/specworks/skills/_shared/start-implement.md` and the design, test and
code `SKILL.md`) are Markdown, which is never scanned for tags; R2 covers
`start-implement.md`.

## Summary

The code matches REQ-INTEG-007 and design.md: every criterion's test checks
its THEN, the suite passes (840 tests), and `specworks skills` leaves
`.claude/skills/` unchanged. Two findings are open: R1 (spec-gap, back to
specify) the `specworks update` ordering has no requirement or test; R2
(quality, back to design) `start-implement.md` depends on having no trailing
newline.
