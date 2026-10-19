# Design: specs

## Overview

Specs and traceability: parsing spec files (delta and living), capabilities as
the specs see them, format checks, tasks, the trace matrix, and merging deltas
into living specs at close. This design covers only what has been specified so
far, the tag scan's ignore markers. The rest of the capability is recorded when
its behaviour is specified.

## Decisions

### Ignore markers are filtered in the scan

`scan_tags` (`trace.py`) skips ignored lines before it builds any `Tag`, so
every consumer gets the same filtered list: the trace matrix, the gaps, unknown
tags, review and validate. The alternatives were an `ignored` flag on `Tag`, or
a filter in the unknown-tag check only. Both were rejected because a consumer
that forgot the flag would count a sample as coverage. (ignore-sample-tags)

### Markers are plain text, block markers must stand alone

A line holding `specworks: ignore-tags` (not followed by `-`) is skipped,
whatever the comment syntax. A block runs from `specworks: ignore-tags-start` to
`specworks: ignore-tags-end`, or to the end of the file, and never into the next
file. A start or end marker counts only when nothing but comment punctuation
surrounds it, so docs and docstrings can quote the markers. An end with no start
is ignored. (ignore-sample-tags)

## Interfaces

- `src/specworks/specs/trace.py`: `scan_tags(ws: Workspace) -> list[Tag]`, the
  tags of the workspace with marked lines left out (REQ-SPECS-001..003).

## Constraints

- The markers never change what a project without them sees.
- Tags and markers are language-agnostic: no knowledge of comments or string
  literals.
