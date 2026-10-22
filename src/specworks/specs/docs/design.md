# Design: specs

## Overview

Specs and traceability, in `src/specworks/specs`:
- **Spec files** (`specfile.py`): parsing delta and living specs into
  requirements and criteria, and what makes a living spec broken.
- **Capabilities** (`capabilities.py`): a capability as the specs see it: its
  reference, ID prefix, delta path, living spec and next free ID.
- **Check** (`check.py`): `specworks check` on a change's proposal, delta
  specs, tasks and diagrams.
- **Tasks** (`tasks.py`): reading tasks.md, each task's half, and ticking tasks.
- **Trace** (`trace.py`): the tag scan, the trace matrix, its gaps and unknown
  tags.
- **Merge** (`merge.py`): merging deltas into living specs and archiving the
  change at close.

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

### Living specs are edited as text

Close splices requirement blocks into the living spec instead of re-rendering
it: ADDED blocks go at the end of `## Requirements`, MODIFIED ones replace
their block in place, REMOVED ones are deleted. Everything else (other sections,
notes, code fences, spacing) stays as written, and blank lines are tidied only
where a block is spliced in. A living spec the parser would misread is refused
before anything is written. The tables specworks generates (the requirements.md
index, traceability.md) pass every title through `table_cell`, which escapes a
`|` so it stays in its cell; spec.md keeps titles as written.
(baseline-specs, table-pipe-in-title)

### IDs are never reused

requirements.md keeps a `## History` line per close. A removed requirement
leaves the living spec but stays in that History, so the next free ID counts
it, and `check` refuses to ADD it again. The next ID also counts every active
change's delta, so two changes planned at once don't pick the same number.
Each History line holds the close's local date and time, so `check` can tell a
close earlier the same day from one after a change started, when it warns that
a MODIFIED block may be out of date; a line that holds only a day (written
before this) is compared by day. (baseline-specs, same-day-modified-warning)

### A clash fails only the later change

When two active changes ADD the same ID, or MODIFY or REMOVE the same
requirement, only the one that started later (by start time, then name) gets
an error; the earlier one gets a warning. Two changes thus never block each
other, and the one that closes second copies the block again from the living
spec. (baseline-specs)

### A file's module decides how it is scanned

Each file belongs to the innermost module holding it, and that module's
`test_globs` and `source_globs` decide whether it is a test and whether it is
scanned. Without globs, a test is recognised by its name or folder, and
documentation is not scanned, so a tag quoted in a README is not coverage.
(baseline-specs)

### Tasks carry their half as a text marker

A leading `[test]` or `[code]` (any case) puts a task in that half of
implement; it stays in the task's text, and a task with no marker belongs to
design. Each half's gate counts only its own tasks, while validate still needs
every task done. `check` warns when a change with criteria has no `[test]`
task, or one with requirements has no `[code]` task, so a task list written
without markers is noticed. (parallel-test-code)

### Issues are built by constructors, checks are split by concern

`Issue.level` is `Literal["error", "warning"]`, and `Issue.error(file, line,
message)` and `Issue.warning(...)` build issues, so call sites never repeat the
level string. `_check_delta` is one private function per concern (delta format,
living spec and registration, conflicts with other active changes, the
per-requirement rules, requirement body), called in the original order so issue
order is unchanged. Alternative: a `DeltaChecker` class, rejected as more
structure than the shared state needs. (refactor-check-delta)

### Close is all or nothing

Close computes every living spec and index first, checks the archive folder,
then writes; if writing or archiving fails, every living file is put back as it
was. (baseline-specs)

## Interfaces

- `src/specworks/specs/specfile.py`: `parse_spec(text) -> SpecDoc`,
  `living_problems(doc)`, `Requirement.markdown()`, `id_prefix`, `ac_parent`,
  `find_ids`, `table_cell(text)`.
- `src/specworks/specs/capabilities.py`: `CapabilityRef`, `resolve_ref(ws, ref)`,
  `resolve_delta`, `next_id(ws, cap)`, `describe(ws, cap)`, `retired_ids`,
  `modified_since`.
- `src/specworks/specs/check.py`: `check_change(ws, change) -> (ChangeSpecs, [Issue])`,
  `collect`, `other_deltas`, `Issue` (`level`: `"error"` or `"warning"`;
  `Issue.error(file, line, message)`, `Issue.warning(file, line, message)`).
- `src/specworks/specs/tasks.py`: `parse_tasks(text)`, `read_tasks`,
  `set_done(change_path, nums, done)`, `Task` (`half`: `"test"`, `"code"` or
  `""`; in `to_dict()` too).
- `src/specworks/specs/trace.py`: `scan_tags(ws: Workspace) -> list[Tag]`, the
  tags of the workspace with marked lines left out (REQ-SPECS-001..003, 011);
  `build_matrix`, `gaps`, `unknown_tags`, `to_markdown`, `Analysis`.
- `src/specworks/specs/merge.py`: `plan_merge(...) -> [CapabilityMerge]`,
  `close_change(merges, change, archive_root)`, `archive_change`.

## Constraints

- The markers never change what a project without them sees.
- Tags and markers are language-agnostic: no knowledge of comments or string
  literals.
