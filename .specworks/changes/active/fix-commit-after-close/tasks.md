# Tasks: fix-commit-after-close

## 1. Committing an archived change

- [ ] 1.1 [test] Tests in `tests/test_commit.py` for AC-PROJ-024.6 (after `specworks close`, the phase commit holds the archive folder and the removal of the active folder, subject `<ref>: close`), AC-PROJ-024.7 (the change's own `.change.yaml`, dirty in the record and changed again, is committed and not in `already_dirty`), AC-CLI-012.4 (`commit --change <ref> --json` after close exits 0 with the subject `<ref>: close`) and AC-CLI-012.3 (a ref neither active nor archived is an error), tagged `@ac`; verify the new ones fail before 1.2
- [ ] 1.2 [code] `commit` in `src/specworks/cli/changes.py` falls back to `archived_as`; `commit_phase` gives a `done` change the subject `<ref>: close` and leaves the change's own folder out of `already_dirty` (REQ-PROJ-024, REQ-CLI-012), tagged `@req`; verify `specworks run lint` passes and, in a scratch project, `specworks close` then `specworks commit` commits the archive
