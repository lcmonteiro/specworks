# Review: improve-test-phase

Base: `origin/main`

## Findings

None.

## Changed files without tags

- `tests/test_skills.py`: wording tests for the pinned phrases of design.md; the skills have no capability (`specworks skip-specs`), so the tests carry no `@ac`.

## Summary

No drift. The four test rules (risk, negative cases, integration, quality) sit in step 4 of `specworks-test` and the missing scenarios in step 7's report, and the error or limit scenario rule in step 4 of `specworks-specify`, all verbatim from design.md; the installed copies in `.claude/skills/` carry the same changes, and the four pinned phrases are tested. The full suite passes (1282 tests). No spec, design or code change; nothing sent back.
