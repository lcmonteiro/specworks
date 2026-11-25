# Tasks: pr-review-with-inspect

## 1. Inspection notes by turn (workflow)

- [x] 1.1 Add `src/specworks/workflow/inspection.py` with `InspectionNote`, `InspectionTurns` (`__bool__`, `to_dict`) and `inspection_turns(change)` as stubs (REQ-FLOW-020); verify `uv run mypy` passes
- [ ] 1.2 [test] Write failing tests in `tests/workflow/` for AC-FLOW-020.1, AC-FLOW-020.2, AC-FLOW-020.3, AC-FLOW-020.4, each tagged `@ac`; verify they fail on the stub, not on setup
- [x] 1.3 [code] Implement `inspection_turns` from `read_findings` of the inspection artifact: open readable findings, `inspect` route to the reviewer, any other to the author, in file order (REQ-FLOW-020) tagged `@req REQ-FLOW-020`; verify `uv run ruff check src && uv run mypy`, and `inspection_turns` on the archived `unify-check-findings` gives no note

## 2. Inspection's open state (workflow)

- [ ] 2.1 [test] Write failing tests in `tests/workflow/` for AC-FLOW-001.6 (ready, done, open) and AC-FLOW-001.7 (open, then done once confirmed, archived), tagged `@ac`; verify they fail on the `open` assertion
- [x] 2.2 [code] In `artifact_states`, report inspection as `open` when `inspection_turns(change)` has a note, with a local import naming the `findings → artifacts` cycle (REQ-FLOW-001) tagged `@req REQ-FLOW-001`; verify `uv run ruff check src && uv run mypy`, and `specworks status --change unify-check-findings` still shows inspection `done`

## 3. status, list --archived and context (cli)

- [x] 3.1 Add `inspection_dict(change)` and `inspection_hint(ref, turns)` in `src/specworks/cli/output.py` as stubs, and `inspected` in `context`'s data (REQ-CLI-025, REQ-CLI-027); verify `uv run mypy` passes
- [ ] 3.2 [test] Write failing tests in `tests/cli/` for AC-CLI-025.1, AC-CLI-025.2, AC-CLI-025.3, with the pinned status lines of design.md, tagged `@ac`; verify they fail on the missing `inspection`
- [ ] 3.3 [test] Write failing tests in `tests/cli/` for AC-CLI-026.1 (pinned list suffix) and AC-CLI-027.1, AC-CLI-027.2, AC-CLI-027.3 (pinned `inspected:` lines), tagged `@ac`; verify they fail on the missing keys
- [x] 3.4 [code] Implement `inspection_dict` and `inspection_hint`, and add `inspection` to `status` of an archived change with the pinned lines (REQ-CLI-025) tagged `@req REQ-CLI-025`; verify `uv run specworks status --change unify-check-findings --json` has no `inspection`
- [x] 3.5 [code] Add `inspection` and the pinned suffix to `list --archived` rows (REQ-CLI-026) tagged `@req REQ-CLI-026`; verify `uv run specworks list --archived` prints as before for this repository
- [x] 3.6 [code] Add `inspected` to `context` (current module, every module with `--all`) and its text lines (REQ-CLI-027) tagged `@req REQ-CLI-027`; verify `uv run specworks context --json` has `"inspected": []`

## 4. Skills (text, no capability)

- [ ] 4.1 [test] Add assertions to `tests/test_skills.py` for the pinned skill wording of design.md (inspect, reopen, onboard, refine), which read REQ-CLI-025 and REQ-CLI-027's output; verify they fail on today's skills
- [x] 4.2 [code] Update `src/specworks/skills/specworks-inspect/SKILL.md`: the PR review process, and on a closed change with notes commit, offer the push (`pushing` include), request changes, never offer the reopen (REQ-CLI-025); verify `uv run specworks skills` refreshes `.claude/skills/` with no other diff
- [x] 4.3 [code] Update `src/specworks/skills/specworks-reopen/SKILL.md`: read `inspection.author` from `status --json`; when present, reason `inspection notes <IDs>`, phase `specify` if a step is specify else `review`, one confirmation, no R findings; otherwise ask why as today (REQ-CLI-025); verify `uv run specworks skills` refreshes the installed copy
- [x] 4.4 [code] Update `specworks-onboard` and `specworks-refine` (step 1) to point an `inspected` change to the skill its notes wait for before new work (REQ-CLI-027); verify `uv run specworks skills` refreshes the installed copies

## Workflow follow-up

- The GitHub wiki page on reviewing pull requests describes the same process.
