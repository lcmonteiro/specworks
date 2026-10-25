# Review: skill-frontmatter-multiline

Base: `origin/main`

## Findings

None.

Checked against REQ-INTEG-005 (MODIFIED):
- AC-INTEG-005.7: `split_frontmatter` appends each indented line to the key
  above it, so `render_skill` keeps or drops a key with all its lines, and
  `render_prompt` copies the whole description, with no change to either. The
  multi-line test checks all three copies: Copilot keeps the folded description
  (with its `Use when:` line) and drops the two-line `allowed-tools`, Claude
  Code keeps everything, and the prompt file keeps the description. It failed
  before the fix.
- Single-line frontmatter is unchanged. A test per packaged skill (12)
  compares the Copilot and Claude Code copies with the one-line rule, so
  refreshing an installed project changes nothing.
- All 63 tests in `tests/test_skills.py` pass (AC-INTEG-005.1 to .6 included),
  and so do the full suite and lint.
- Known limit, as the spec words it ("the indented lines that continue it"): an
  empty line inside a block value isn't indented, so it isn't kept, and a
  folded value loses a paragraph break but none of its text. No packaged skill
  has one.

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

A multi-line frontmatter value now travels whole with its key into every copy
of a skill, and today's output is unchanged. No drift.
