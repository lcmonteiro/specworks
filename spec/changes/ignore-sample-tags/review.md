# Review: ignore-sample-tags

Base: `origin/main`

## Findings

None.

Checked in both directions against the delta spec and design.md:
- REQ-SPECS-001: `IGNORE_LINE_RE` (`specworks: ignore-tags` not followed by `-`
  or a word character) skips a marked line wherever the marker sits. The tests
  cover `#` and `//` syntax.
- REQ-SPECS-002: `_tag_lines` opens and closes a block only on a line with no
  other letters or digits (`_is_marker`). A start with no end runs to the end of
  the file, because the state is per call, i.e. per file. A stray end is
  ignored. The tests cover `#` and `/* */` blocks, an unclosed start followed by
  another file, a marker quoted in prose, and an end with no start.
- REQ-SPECS-003: the filter sits in `scan_tags`, so the matrix, the gaps,
  unknown tags, review and validate all see the same filtered tags, as the
  design decided.
- AC-SPECS-002.3 and AC-SPECS-002.4 passed before the code phase. That's
  expected: they assert that a tag is still found, so they fail if the
  implementation ignores too much, which is what they guard against.
- `## Interfaces` says None: `scan_tags` keeps its signature and the helpers are
  private.
- Coverage of the full suite: 97% (CI needs 95%).

## Changed files without tags

- `tests/helpers.py`: only `# specworks: ignore-tags` markers next to fixture
  tags (task 4.1). The fixture content is unchanged.
- `tests/test_design_phase.py`: same, markers only (task 4.1).
- `tests/test_review_phase.py`: same, markers only (task 4.1).
- `tests/test_specified.py`: same, markers only (task 4.1).
- `tests/test_test_phase.py`: same, markers only (task 4.1).
- `tests/test_walkthrough.py`: an ignore block around the walkthrough
  project's sample tests and code (task 4.1).

## Summary

No drift between the code, the spec and the design. One process exception,
agreed with the user: `gate test` couldn't pass before this change's code
existed, since its only failing check was the sample tags this change makes
ignorable. The change was therefore moved to code by hand
(`specworks phase code`). The code and review gates ran in full and pass, with
no unknown tags.

Candidates for later changes: report the number of ignored tags in
`specworks trace`; warn about an unclosed `ignore-tags-start`; describe the
markers on the wiki's trace page and in the test-phase skill (for projects
whose tests write tagged fixtures).

The diff against `origin/main` also holds the paused `baseline-project`
change's `@ac` tags and test (tests/test_cli.py, test_modules.py, …). Those
belong to that change, which records them.
