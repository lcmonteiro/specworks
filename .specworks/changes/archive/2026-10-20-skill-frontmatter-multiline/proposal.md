# Proposal: skill-frontmatter-multiline

## Why

When a skill is installed, a frontmatter value written over several lines
loses everything after its first line. Copilot copies and prompt files would
get an empty `description` (reproduced; latent today; suspected bug 10 of
`baseline-integrations`; refinement.md, option A).

## What Changes

- In a skill's frontmatter, an indented line after a key belongs to that key:
  it is kept when the key is kept and dropped when the key is dropped, in the
  tool copies and in the Copilot prompt file.
- Single-line frontmatter (every packaged skill today) is copied byte-for-byte
  as before.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `integrations`: REQ-INTEG-005 "Installing the skills" MODIFIED. Its
  description says a kept or dropped key takes its whole value, and it gets a
  new criterion, AC-INTEG-005.7.

## Impact

`src/specworks/tools/skills.py` (`split_frontmatter`) and
`tests/test_skills.py`. No API, data or dependency change.

## Out of Scope

- YAML forms that don't use indentation for continuation (flow mappings,
  quoted values spanning lines with no indent).
- Rewriting frontmatter through a YAML parser (option C).
