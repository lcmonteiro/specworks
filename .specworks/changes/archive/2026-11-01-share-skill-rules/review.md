# Review: share-skill-rules

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **spec-gap** update_skills now fills in every skill before removing stale ones, so `specworks update` with a failing include changes nothing on disk (design.md, Filling in), but REQ-INTEG-007 and AC-INTEG-007.6 name only `specworks skills`, and no test fails if update_skills goes back to removing first (src/specworks/tools/skills.py:329)
  - **Proposal**: back to specify: name `specworks update` next to `specworks skills` in REQ-INTEG-007 and add AC-INTEG-007.8 (a packaged include fails, `specworks update` exits 1, no skill folder removed or changed), with its [test] task; the code already does it
  - **Decision**: back to specify: add specworks update to REQ-INTEG-007 with AC-INTEG-007.8 (a failing include during update changes nothing on disk) and its test
  - done in specify: REQ-INTEG-007 now covers specworks update (writes, changes and removes no skill on a failure); added AC-INTEG-007.8 and task 3.1
  - done in design: no API change: update_skills keeps its signature and already fills in every skill before removing stale ones (design.md, Filling in); AC-INTEG-007.8 is reached through specworks update
  - confirmed in review: confirmed: REQ-INTEG-007 names specworks update, AC-INTEG-007.8 is tested at tests/test_skills.py:1055 and fails when update_skills removes stale skills before filling in (checked by swapping the order)
- [x] R2 **quality** start-implement.md relies on having no trailing newline: the code skill keeps a blank line after the include and the test skill a line starting with a space (' Tests built on an undecided API...') to rebuild the original text; an editor or end-of-file fixer adding the newline silently changes both installed skills, and no test checks the repo's installed copies (src/specworks/skills/_shared/start-implement.md:10, src/specworks/skills/specworks-test/SKILL.md:48-49, src/specworks/skills/specworks-code/SKILL.md:38-39)
  - **Proposal**: back to design: give start-implement.md a `{{note}}` after 'themselves fail).' and a trailing newline, as back-from-review.md does; the test skill passes note=" Tests built on an undecided API test the wrong thing.", the code skill note="", and both drop the extra line; installed copies stay byte for byte the same
  - **Decision**: back to design: give start-implement.md a {{note}} placeholder and a trailing newline (test: note with its extra sentence, code: note=""), dropping the extra lines in both skills; installed copies unchanged byte for byte
  - done in design: design.md (The shared files): start-implement.md ends with {{note}} and a final newline; test passes note with its extra sentence, code note="", no extra lines after the include; no API change
  - done in implement: start-implement.md ends with {{note}} and a final newline; specworks-test passes note=" Tests built on an undecided API test the wrong thing.", specworks-code note="", and neither keeps an extra line after the include; uv run specworks skills leaves .claude/skills/ unchanged
  - confirmed in review: confirmed: start-implement.md ends with {{note}} and a final newline, test and code pass note and keep no extra line after the include, and uv run specworks skills leaves .claude/skills/ unchanged

## Changed files without tags

None: `specworks review` lists no untracedSource or untracedTests. The skill
files (`src/specworks/skills/_shared/back-from-review.md`,
`src/specworks/skills/_shared/start-implement.md` and the design, test and
code `SKILL.md`) are Markdown, which is never scanned for tags; R2 covers
`start-implement.md`.

## Summary

Cycle 2: both findings from cycle 1 are carried out and closed. R1
(spec-gap): REQ-INTEG-007 now covers `specworks update`, and the test for
AC-INTEG-007.8 fails if `update_skills` removes stale skills before filling
in. R2 (quality): `start-implement.md` ends with `{{note}}` and a final
newline, and neither skill keeps an extra line after the include. Reading the
diff again found no new drift: the code matches REQ-INTEG-007 and design.md,
every criterion's test checks its THEN, the suite passes (841 tests), lint
and typecheck pass, and `specworks skills` leaves `.claude/skills/`
unchanged. No open findings.
