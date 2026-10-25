# Review: baseline-integrations

Base: `origin/main`

## Findings

None.

A baseline changes no behaviour. In `src/specworks/tools` this change adds only
`# @req REQ-INTEG-…` comment lines (diagrams: `source_hash`, `stamp`, `render`,
`state`, `find_d2`; skills: `parse_tools`, `read_skill`, `render_skill`,
`render_prompt`, `install_skills`). In the tests it adds only
`# @ac AC-INTEG-…` comment lines, plus one new test,
`tests/test_skills.py::test_an_empty_tool_list_is_rejected` (AC-INTEG-004.4),
which passes against the current code.

## Changed files without tags

The base `origin/main` also lacks the closed changes `ignore-sample-tags`,
`baseline-project` and `baseline-workflow`, which are on this branch:

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

The existing behaviour of `integrations` is recorded as REQ-INTEG-001..005 (20
criteria). The existing tests are tagged, one test was added (AC-INTEG-004.4),
and the code is tagged. No drift was found. Left out of scope (see proposal.md):
the rules written in the skills' text (a candidate `skills` capability), and
three suspected bugs: an `<?xml` declaration that never closes, old skills that
are never removed, and multi-line frontmatter values.
