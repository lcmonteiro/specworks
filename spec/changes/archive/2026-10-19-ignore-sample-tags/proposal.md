# Proposal: ignore-sample-tags

## Why

Sample tags that tests write as fixture content (`write_text("# @req REQ-AUTH-003\n")`)
are scanned as real tags. Their prefixes match no capability, so the blocking
unknown-tag check fails in this repository, and every baseline is blocked
(see refinement.md, option A). A project needs a way to mark such samples, in
the source next to them, so the scan skips them.

## What Changes

- The tag scan skips tags on a line holding the marker `specworks: ignore-tags`,
  in any comment syntax, anywhere on the line.
- The tag scan skips every line from a `specworks: ignore-tags-start` marker to
  a `specworks: ignore-tags-end` marker, in the same file. A start with no end
  runs to the end of the file.
- A start or end marker counts only on a line with no other words: a line that
  quotes it in prose (docs, docstrings) doesn't open or close a block. An end
  with no start is ignored.
- Ignored tags count neither as test or code coverage nor as unknown tags.
- This repository's sample tags (tests and the `trace.py` docstring) get the
  markers, and the `trace.py` docstring documents them.
- Projects that don't use the markers see no change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `specs`: ADDED requirements for ignore markers in the tag scan
  (REQ-SPECS-001..003). The capability has no living spec yet; its baseline
  records its other behaviour later.

## Impact

- `src/specworks/specs/trace.py`: `scan_tags` gains the markers, and its
  docstring documents them. The function signatures and the trace outputs keep
  their shape.
- Tests: new tests for the markers, plus markers added next to the sample tags
  in `tests/*.py`. The fixture content doesn't change, because the markers are
  Python comments outside the strings.
- No new dependency or config key.

## Out of Scope

- Reporting how many tags were ignored in `specworks trace` (possible
  follow-up).
- Warning about a stray `ignore-tags-end` or an unclosed start.
- Excluding whole files or folders from the scan with a config setting.
- Recognising comments or string literals by language.
