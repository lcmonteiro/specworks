# Proposal: module-interface-paths

## Why

For a change in a module, the design gate accepts an Interfaces file found at
the workspace root, so a missing stub passes when a top-level file has the same
path (reproduced; suspected bug 6 of `baseline-workflow`; refinement.md,
option C).

## What Changes

- A file named under Interfaces counts only if it exists inside the change's
  module folder. It may be written module-relative (`src/invoices.py`) or
  workspace-relative (`services/billing/src/invoices.py`).
- Top-level changes behave as today, since their module folder is the workspace
  root.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workflow`: REQ-FLOW-006 "Gate design" MODIFIED. Its description states where
  a named file must be, and it gets a new criterion, AC-FLOW-006.6.

## Impact

`src/specworks/workflow/gate.py` (`interface_files_exist`) and
`tests/test_design_phase.py`. No API, data or dependency change.

## Out of Scope

- Checking that a stub's symbols (class or function names) exist.
- The other suspected bugs.
