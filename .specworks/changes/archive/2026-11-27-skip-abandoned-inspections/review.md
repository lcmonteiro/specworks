# Review: skip-abandoned-inspections

Base: `pr-review-with-inspect`

## Findings

None.

- REQ-CLI-025 / REQ-CLI-026: `inspection_dict` (`src/specworks/cli/output.py:79`)
  returns `{}` when `change.abandoned` is set, as design.md's Decision says;
  `status` and `list --archived` go through it unchanged.
- REQ-CLI-027: `context` (`src/specworks/cli/project.py:247`) builds
  `inspected` from `inspection_dict`, so the three commands share one rule;
  its text line reads `inspection_turns` again for the kept changes only, the
  trade-off design.md records.
- `## Interfaces` says none: `inspection_dict(change) -> dict` keeps its
  signature.
- AC-CLI-025.4, AC-CLI-026.2, AC-CLI-027.4 (`tests/cli/test_inspection_notes.py`)
  abandon a real change with `specworks abandon` and check both the JSON and
  the text. With the change's `src/` diff reverted, all three fail and the
  other ten still pass; with it, all thirteen pass. Full suite: 1372 passed.

## Changed files without tags

- `tests/test_skills.py`: listed only against the default base `origin/main`;
  it belongs to the stacked parent change `pr-review-with-inspect` (skill
  wording, untagged by convention). Against this change's own base
  (`pr-review-with-inspect`) nothing is untraced.

## Summary

The code, the delta specs and design.md agree: one rule in `inspection_dict`
hides an abandoned change's notes from `status`, `list --archived` and
`context`, and the three new criteria are checked by tests that fail without
it. No spec, design or code change; nothing sent back.
