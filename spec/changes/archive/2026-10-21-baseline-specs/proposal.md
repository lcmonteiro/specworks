# Proposal: baseline-specs

## Why

Record the existing behaviour of `specs`. Its living spec holds only the three
tag-ignore requirements of `ignore-sample-tags`; the rest of the capability
(spec files, `check`, tasks, the next ID, the tag scan, the trace matrix and the
merge at close) has no requirements, so later changes can only ADD to it.

## What Changes

- No behaviour change: requirements for what `src/specworks/specs` already
  does, `@ac` tags on the tests that show it, new tests only for criteria no
  test covers, and `@req` tags on the code.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `specs`: REQ-SPECS-004 to REQ-SPECS-014 ADDED (existing behaviour). The
  living spec already has its Purpose and REQ-SPECS-001 to 003, which stay as
  they are.

## Impact

Tags in `tests/` and `src/specworks/specs/`, a few new tests. No code change.

## Out of Scope

Suspected bugs found while reading, each a candidate for its own change:
- `check` warns that a requirement was MODIFIED "after this change started"
  when the other change closed earlier on the same day, before this one
  started: `modified_since` compares days, not times.
- `requirements.md` puts each title in a table cell as written, so a title
  with `|` breaks the index table.

Behaviour other capabilities already specify: the specify gate (`workflow`
REQ-FLOW-004), specs as agreed (REQ-FLOW-005), the `close` command
(`cli` REQ-CLI-007) and diagram rendering (`integrations`).
