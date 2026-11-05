# Tasks: add-reopen-change

## 1. Reopen a closed change (project)

- [x] 1.1 Add `Reopened`, `Change.reopened` and `reopen_change` as stubs in `src/specworks/core/changes.py` (REQ-PROJ-033, REQ-PROJ-034); verify with `uv run mypy`
- [x] 1.2 [test] Write failing tests for AC-PROJ-033.1, AC-PROJ-033.2, AC-PROJ-033.3, AC-PROJ-033.4, AC-PROJ-033.5, AC-PROJ-033.6, AC-PROJ-033.7 and AC-PROJ-033.8 in `tests/project/test_reopen.py`, tagged `@ac`; verify they fail for the right reason (the stub does nothing)
- [x] 1.3 [test] Write failing tests for AC-PROJ-034.1, AC-PROJ-034.2, AC-PROJ-034.3 and AC-PROJ-034.4 in `tests/project/test_reopen.py`, tagged `@ac`; verify they fail for the right reason
- [x] 1.4 [code] Implement `reopen_change` (find the archived change, refuse active, unknown and abandoned ones and a name in use, check the reason and the phase as `set_phase` does, record the dirty files, add the entry, move the folder, restore the metadata when the move fails) and the saving and reading of `reopened` (REQ-PROJ-033, REQ-PROJ-034), tagged `@req`; verify with lint and typecheck, and by reopening a closed sample change from a Python shell and reading its metadata

## 2. A change's own IDs at the second close (specs)

- [x] 2.1 Add `own_ids`, the `exclude` parameter of `modified_since` and the `own` parameter of `apply_delta` as stubs in `src/specworks/specs/capabilities.py` and `src/specworks/specs/merge.py` (REQ-SPECS-017); verify with `uv run mypy`
- [x] 2.2 [test] Write failing tests for AC-SPECS-017.1, AC-SPECS-017.2, AC-SPECS-017.3, AC-SPECS-017.4 and AC-SPECS-017.8 (the checks) in `tests/specs/test_own_ids.py`, tagged `@ac`; verify they fail for the right reason
- [x] 2.3 [test] Write failing tests for AC-SPECS-017.5, AC-SPECS-017.6 and AC-SPECS-017.7 (the merge) in `tests/specs/test_own_ids.py`, tagged `@ac`; verify they fail for the right reason
- [x] 2.4 [code] Implement `own_ids`, and use it in `check` so an own ADDED ID in the living spec and an own REMOVED ID already gone are accepted, and pass `exclude` to `modified_since` (REQ-SPECS-017, REQ-SPECS-006), tagged `@req`; verify with lint and typecheck, and by running `specworks check` on a sample reopened change
- [x] 2.5 [code] Implement the merge: an own ADDED block present in the living spec is replaced in place, listed as MODIFIED and not appended again; an own REMOVED ID already gone is skipped; `plan_merge` passes `own_ids` (REQ-SPECS-017, REQ-SPECS-013), tagged `@req`; verify with lint and typecheck, and by running `specworks close --dry-run` on a sample reopened change

## 3. The reopen command (cli)

- [x] 3.1 Add the `reopen` command as a stub in `src/specworks/cli/changes.py` (REQ-CLI-020); verify with `uv run mypy`
- [x] 3.2 [test] Write failing tests for AC-CLI-020.1, AC-CLI-020.2, AC-CLI-020.3, AC-CLI-020.4, AC-CLI-020.5 and AC-CLI-020.6 in `tests/cli/test_reopen.py`, tagged `@ac`; verify they fail for the right reason
- [x] 3.3 [test] Write failing tests for AC-CLI-021.1, AC-CLI-021.2 and AC-CLI-002.7 in `tests/cli/test_reopen.py`, tagged `@ac`; verify they fail for the right reason
- [x] 3.4 [code] Implement `reopen`: resolve the archived change (saying "active" when it is), require `--reason`, default `--phase review`, call `reopen_change`, print the path and phase, and `--json` with the entry; touch no branch (REQ-CLI-020, REQ-CLI-002), tagged `@req`; verify with lint and typecheck, and by running `specworks reopen --help` and a reopen of a sample closed change
- [x] 3.5 [code] Show the reopen in `status` (the count and the latest reason) and carry `reopened` in `change_dict` in `src/specworks/cli/output.py` (`--json`) only when there are entries (REQ-CLI-021), tagged `@req`; verify with lint and typecheck, and by running `specworks status` on a sample reopened change

## 4. The skill

- [x] 4.1 [test] Write the skill tests in `tests/test_skills.py`: the pinned wording of `specworks-reopen` and of the reopen line in `specworks-refine` and `specworks-specify` (design.md Decisions > Pinned wording), and add `specworks-reopen` to the skills that pick no active change by the shared rule (REQ-CLI-020); verify they fail for the right reason
- [x] 4.2 [code] Write `src/specworks/skills/specworks-reopen/SKILL.md`: pick or ask for the closed change, take the problem, route it to a phase with the table, confirm, run `specworks reopen`, add the finding for a `review` start, commit with `--message "<ref>: reopen"`, offer the next step (REQ-CLI-020); verify the skill loads with `uv run specworks skills --help` and reread it against the Pinned wording
- [x] 4.3 [code] Add the reopen line to the step that loads what exists in `src/specworks/skills/specworks-refine/SKILL.md` and `src/specworks/skills/specworks-specify/SKILL.md`, then run `uv run specworks skills` to refresh the installed copies (REQ-CLI-021); verify `uv run specworks skills` reports them updated
