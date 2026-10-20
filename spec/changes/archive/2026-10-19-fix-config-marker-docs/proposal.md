# Proposal: fix-config-marker-docs

## Why

The `core/config.py` module docstring says "the first line `specworks: 1`" marks
a config, but the code, and the living spec (REQ-PROJ-001), accept an
unindented `specworks: <n>` line anywhere in the file. The docstring is the bug
(suspected bug 2 of `baseline-project`; refinement.md, option A).

## What Changes

- Reword the docstring of `src/specworks/core/config.py` to say that an
  unindented `specworks: <n>` line, anywhere in the file, marks a specworks
  config.
- No behaviour change, so the change has no delta specs (skip-specs).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: REQ-PROJ-001 already states the behaviour.

## Impact

One docstring in `src/specworks/core/config.py`. No code, API, data or
dependency change.

## Out of Scope

- Requiring the marker on the first line (option B: breaking, little gain).
- The other suspected bugs.
