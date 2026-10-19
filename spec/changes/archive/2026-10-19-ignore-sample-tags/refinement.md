# Refinement: ignore-sample-tags

## Problem

specworks' own tests (and the `trace.py` docstring) write example tags, such as
`write_text("# @req REQ-AUTH-003\n")`, as fixture content. The trace scan reads
them as real tags of this repository. Every one has a prefix no capability uses,
so the blocking check "no tag refers to an unknown requirement or criterion"
fails. That blocks `baseline-project`, which is paused in its test phase, and
every later baseline here. Any project whose tests generate tagged code
(specworks-like tools, code generators, linters) has the same problem.

## Context

**Observed:**
- `src/specworks/specs/trace.py` (`scan_tags`) matches `TAG_RE` anywhere on any
  line of a scanned file. It doesn't know about comments or string literals.
  `scan_rule` (`test_globs` / `source_globs`, documentation skipped) only
  decides which files are scanned and which count as tests.
- `unknown_tags` flags a tag whose prefix no capability uses, a malformed ID, or
  an ID under this change's own prefixes that no spec has. `no_unknown_tags` is
  blocking in the test, code and review gates (`workflow/gate.py`) and in
  validate (`workflow/validate.py`).
- In this repository there are about 60 sample tags: about 52 in one-line string
  literals across 11 test files, 3 in a triple-quoted string in
  `tests/test_walkthrough.py`, and 3 in the module docstring of `trace.py`.
  Some samples are deliberate inputs to the unknown-tag tests (`AUHT`, a
  malformed `REQ-AUTH`).
- The same test files also carry real `@ac AC-PROJ-…` tags, so leaving whole
  files out of the scan does not work.
- The `specs` capability (`src/specworks/specs`) owns the trace scan. It has no
  living spec yet (no baseline).

**Assumed:**
- Adding a trailing comment to a Python line that writes a fixture leaves the
  fixture's content unchanged, so no test changes behaviour.
- Projects that don't use the markers see no difference.

## Constraints

- [hard] No change for projects that don't use the markers: the same tags are
  found and the same checks block.
- [hard] Language-agnostic, like the tags themselves: the marker is plain text,
  whatever the comment syntax.
- [hard] Typo detection (`AUHT`, "did you mean AUTH?") keeps blocking outside
  ignored regions.
- [soft] Ignoring must be visible in the source, right next to the samples, and
  never a silent global setting.
- [soft] Keep the `trace` docs (`trace.py` docstring, the wiki) in step with
  the markers.

## Options

### Option A: Ignore markers (line and block)

The scan skips tags on a line holding `specworks: ignore-tags`, and on the lines
from `specworks: ignore-tags-start` to `specworks: ignore-tags-end`; a start
with no end runs to the end of the file. The markers are matched anywhere on the
line, inside any comment syntax. Ignored tags count neither as coverage nor as
unknown.

- **Pros:** Explicit and local. Works in every language. Leaves the check as
  strict as before everywhere else. The block form covers multi-line strings and
  docstrings.
- **Cons:** A new convention to learn and document. About 55 one-line markers
  plus 2 blocks to add in this repository.
- **Effort:** S (scan) + S (marking this repository's samples)
- **Touches:** `specs`

### Option B: An unknown prefix only warns

A tag whose prefix no capability uses stops blocking; unknown IDs under a known
prefix still block.

- **Pros:** No markers and no edits to the tests.
- **Cons:** Prefix typos stop blocking for every project. It changes the check's
  meaning everywhere to fix one repository.
- **Effort:** S
- **Touches:** `specs`, `workflow`

### Option C: Only tags in comments count

A tag counts only after a comment token at the start of the line.

- **Pros:** Samples in strings drop out on their own.
- **Cons:** BREAKING for trailing tags (`x = 1  # @req …`). Relies on guessing
  comment syntax per language. Docstring samples still match.
- **Effort:** M
- **Touches:** `specs`

## Recommendation

**Option A, with both the line and the block form.** The user chose it. It is
the only option that keeps the check as strict as today for everyone else, and
it puts the cost (marking the samples) on the repository that has them.

## Open Questions

- **The docs must not trigger the marker.** The `trace.py` docstring (and any
  doc that explains the markers) will quote `specworks: ignore-tags-start`, and
  a quoted start would open a block. Should the docs show the marker in a way
  that doesn't match, or should a start only count when the line has nothing
  else but a comment? (Who can answer: the design phase, with the user.)
- **A stray `ignore-tags-end`:** should an end with no start be silently
  ignored, or reported as a warning? (Who can answer: the user. The default is
  ignored.)
- **Reporting the ignored tags:** should `specworks trace` show how many tags
  were ignored, so ignoring stays visible? (Who can answer: the user. Nice to
  have, not blocking.)

## Candidate Capabilities

- `specs`: modified. The tag scan gains ignore markers. It has no living spec
  yet, so the new behaviour is ADDED; its baseline later records the rest.
