# Proposal: diagrams-dir-root

## Why

`specworks diagrams --dir` resolves its folder from the working directory, but
the CLI prints docs folders relative to the workspace root, and the close skill
passes one of those. From a subfolder it finds no folder and reports
`no diagrams` with exit 0, so a close run inside a module silently renders
nothing (reproduced; suspected bug 13 of `baseline-cli`; refinement.md,
option A).

## What Changes

- A relative `--dir` is resolved from the workspace root, from any folder of
  the workspace; an absolute path is kept as it is.
- A `--dir` folder that doesn't exist fails, naming the folder it looked for,
  instead of reporting no diagrams.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: REQ-CLI-008 "diagrams" MODIFIED. Its description says `--dir` is
  relative to the workspace root and must exist, and it gets new criteria
  AC-CLI-008.6 and AC-CLI-008.7.

## Impact

`src/specworks/cli/specs.py` (`diagrams`) and its tests. The close skill's
`specworks diagrams --dir "<docsPath>"` now works from any folder, unchanged. No
API, data or dependency change.

## Out of Scope

- Other options that take a path relative to the working directory (`init
  <path>`, `module add <path>`): those are shell paths a user types where they
  stand.
