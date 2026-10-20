# Tasks: module-interface-paths

## 1. Interface files inside the change's module

- [ ] 1.1 Write a failing test in `tests/test_design_phase.py` for AC-FLOW-006.6 (a `billing` change naming `src/invoices.py`, present only at the workspace root; then in the module under both forms) tagged `@ac`; verify it fails because the gate counts the top-level file
- [ ] 1.2 In `interface_files_exist`, count a path only if, read relative to the module folder or the workspace root, it names an existing file inside the module folder (REQ-FLOW-006) tagged `@req REQ-FLOW-006`; verify the 1.1 test and the existing AC-FLOW-006.x tests pass
