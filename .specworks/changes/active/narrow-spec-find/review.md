# Review: narrow-spec-find

Base: `origin/main`

## Findings

None.

The tests (902) pass against the code on the first run. `search_requirements`, `RequirementSearch`,
`BroadTerm` and the extended `find_requirements` and `spec find` match `## Interfaces` in design.md
(names, fields, the `ConfigError` for a blank term). The markup is removed only at line starts, before
comparing, and the reported `text` stays the whole stripped line (REQ-SPECS-016, AC-SPECS-016.7). Each term
counts a requirement once, in the same scan, with `count * 2 > searched` (AC-SPECS-016.8). The CLI prints the
warning after the matches, exits 0, and adds `broad` to `--json`, empty for a narrow term (REQ-CLI-016,
AC-CLI-016.5). On this repo, `spec find requirement when` no longer matches every requirement (`when`: 47 of 81,
reported as broad).

## Changed files without tags

- None: `specworks review` lists no file under untracedSource or untracedTests.

## Summary

No drift between the code, the delta specs and design.md. Nothing changed in the code, specs or design,
and nothing goes back to an earlier phase. Out of scope (could be a later change): a line in a requirement's text
that itself starts with a bold `**When**` loses that word too, as design.md's Decision allows.
