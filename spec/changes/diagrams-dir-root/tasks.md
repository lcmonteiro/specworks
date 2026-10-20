# Tasks: diagrams-dir-root

## 1. `--dir` relative to the workspace root

- [ ] 1.1 Write failing tests in `tests/test_diagrams.py` for AC-CLI-008.6 (`diagrams --dir <root-relative folder> --check` from inside a module reports that folder's diagrams) and AC-CLI-008.7 (a missing folder fails with `no folder`), tagged `@ac`; verify they fail because the path is read from the working directory and a missing folder reports no diagrams
- [ ] 1.2 In `diagrams`, resolve a relative `--dir` from `ws.root` and refuse a folder that doesn't exist (REQ-CLI-008) tagged `@req REQ-CLI-008`; verify the 1.1 tests and the existing AC-CLI-008.x tests pass
