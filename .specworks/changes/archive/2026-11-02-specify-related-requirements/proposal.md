# Proposal: specify-related-requirements

## Why

Specify has no step that finds the living requirements already describing
what a change touches, so they stay unchanged and contradict the delta
until review sends the change back (three of four findings in
add-branch-default). A search the agent can run, and a place in the
proposal to record each match, catch them at specify instead.

## What Changes

- New `specworks spec find <term>... [--json]`: every living requirement of
  the workspace (every module) whose title, text or scenarios contain any
  term, literal and case-insensitive, with its capability ref, ID, title and
  first matching line (path relative to the workspace root, line number).
  No match is an empty result.
- The specify skill, step 2, runs `spec find` with the change's terms
  (commands, flags, config keys, file names) and decides per match: a
  MODIFIED block in the delta, or a one-line reason to leave it; step 5's
  table lists them next to the new requirements.
- The proposal template and instruction gain a `## Related requirements`
  section: each match as `REQ-… modified` or `REQ-… left: <reason>`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `specs`: adds REQ-SPECS-016 (finding living requirements by term).
- `cli`: adds REQ-CLI-016 (the `spec find` command).

## Related requirements

Found with `specworks spec find "spec show" "spec list" proposal`:

- REQ-SPECS-008 left: it requires Why, What Changes and Capabilities; the
  new section is guidance and stays optional for `check`.
- REQ-SPECS-010 left: `spec show` keeps its behaviour.
- REQ-CLI-004 left: it covers `context`, `list` and `module list`, not the
  `spec` commands.

## Impact

- `src/specworks/specs/capabilities.py` (or a sibling): the search.
- `src/specworks/cli/specs.py`: the command.
- `src/specworks/templates/proposal.md`, the proposal instruction in
  `src/specworks/schema.yaml`, `src/specworks/skills/specworks-specify/SKILL.md`
  and its installed copy.

## Out of Scope

- Searching active changes' deltas.
- Fuzzy or regular-expression matching.
- A `specworks check` warning for unmodified related requirements.
- Making `## Related requirements` required by `check`.
