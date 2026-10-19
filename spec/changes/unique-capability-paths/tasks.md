# Tasks: unique-capability-paths

## 1. Unique docs folders

- [x] 1.1 Write failing tests for AC-PROJ-016.1, AC-PROJ-016.2, AC-PROJ-016.3 (load a workspace with a shared, a cross-module and a nested path) tagged `@ac`; verify .1 and .2 fail because the workspace still loads, and .3 passes
- [x] 1.2 Write a failing test for AC-PROJ-016.4 (`capability add` on a taken path) tagged `@ac`; verify it fails because the capability is registered
- [ ] 1.3 Refuse a workspace whose capabilities share a resolved docs folder, next to the ID-prefix check (REQ-PROJ-016) tagged `@req REQ-PROJ-016`; verify the 1.1 tests pass
- [ ] 1.4 Refuse `capability add` before writing when the new capability's docs folder is taken, naming its owner (REQ-PROJ-016) tagged `@req REQ-PROJ-016`; verify the 1.2 test passes and the full suite is green
