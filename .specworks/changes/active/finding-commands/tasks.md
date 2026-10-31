# Tasks: finding-commands

## 1. Writing findings

- [ ] 1.1 Add the stubs in design.md's Interfaces in `src/specworks/workflow/review.py` (`FindingError`, `add_finding`, `decide_finding`, `mark_finding_done`, `close_finding`) (REQ-FLOW-016); verify `specworks run lint` passes
- [ ] 1.2 [test] Tests for AC-FLOW-016.1 (a new finding is R3, routed, its Proposal line, R1 and R2 unchanged), AC-FLOW-016.2 (no review.md: created with the template's headings and no example lines, the finding as R1), AC-FLOW-016.3 (back to design routes it; accepted replaces the Decision and ticks), AC-FLOW-016.4 (done in specify routes to design and stays open; close ticks and the review gate has no open finding), AC-FLOW-016.5 (each refusal, file unchanged) and AC-FLOW-016.6 (a `*` bullet with a bold ID and HTML comments kept byte for byte), asserting the pinned lines of design.md, tagged `@ac`; verify they fail on the stubs
- [ ] 1.3 [code] Implement the four writers in `src/specworks/workflow/review.py` as design.md decides (edit, read back, write or refuse) with its pinned lines (REQ-FLOW-016), tagged `@req`; verify `specworks run lint` passes and, on a sample change, each writer's result reads back with `specworks cycle --change <ref>`

## 2. The finding commands

- [ ] 2.1 Add `finding_app` in `src/specworks/cli/app.py` and the four command stubs in `src/specworks/cli/workflow.py` (REQ-CLI-011); verify `specworks finding --help` lists add, decide, done and close
- [ ] 2.2 [test] Tests for AC-CLI-011.1 (the four commands in turn with `--json`: exit 0, ID, state, step and the relative path) and AC-CLI-011.2 (`finding decide R9` with `--json`: an error naming R9, exit 1, file unchanged), tagged `@ac`; verify they fail on the stubs
- [ ] 2.3 [code] Implement the four commands over the writers, with `--change` and `--json` and errors as values (REQ-CLI-011), tagged `@req`; verify `specworks run lint` passes and `specworks finding add` on a sample change prints the new finding

## 3. The skills use the commands

- [ ] 3.1 [test] Wording checks in `tests/test_skills.py`: `specworks-review` adds findings with `specworks finding add` and ticks with `specworks finding close`; `specworks-build` step 3 and `_shared/phase-subagents.md` write Decisions with `specworks finding decide`; `specworks-specify` and the design, test and code skills record their part with `specworks finding done`; verify they fail before 3.2 (REQ-CLI-011)
- [ ] 3.2 [code] Edit those skills to use the commands, and refresh the installed copies with `uv run specworks skills` (REQ-CLI-011); verify `specworks run lint` passes and the installed copies are current
