# Tasks: add-inspect-skill

## 1. Inspection as a check artifact

- [x] 1.1 Add the `inspection` artifact to `schema.yaml` and `templates/inspection.md` per design.md Interfaces (REQ-FLOW-018, REQ-FLOW-001); verify `uv run ruff check src tests && uv run mypy`
- [x] 1.2 [test] Write failing tests for the three declared check artifacts, an open I1 blocking neither the review gate nor validate, and inspection's status (ready and optional, then done), tagged `@ac AC-FLOW-018.1`, `@ac AC-FLOW-018.4`, `@ac AC-FLOW-001.6`; keep AC-FLOW-018.2, 018.3 and AC-FLOW-001.1 to 001.5 passing; verify the new ones fail before 1.3
- [x] 1.3 [code] Implement what 1.1 declares so the check artifacts list inspection, blocking no gate (REQ-FLOW-018, REQ-FLOW-001) tagged `@req REQ-FLOW-018`, `@req REQ-FLOW-001`; verify `uv run specworks status --change add-inspect-skill` lists inspection

## 2. Routing back to inspect

- [x] 2.1 Add `question` to `TYPE_PHASE`, the `artifact` parameter of `_next_step` and `WAITING_STEPS` in `cycle.py` as stubs (REQ-FLOW-010, REQ-FLOW-012); verify `uv run ruff check src tests && uv run mypy`
- [x] 2.2 [test] Write failing tests for a `question` I1 routed to review, an I1 routed code → review → inspect (a V the same → validate), and a change whose only open finding waits for inspect (no cycle, next close), tagged `@ac AC-FLOW-010.12`, `@ac AC-FLOW-010.13`, `@ac AC-FLOW-012.11`; keep AC-FLOW-010.1 to 010.11 and AC-FLOW-012.1 to 012.10 passing; verify they fail on the stubs
- [x] 2.3 [code] Implement the step after review from the finding's artifact and findings waiting for validate or inspect left out of the cycle (REQ-FLOW-010, REQ-FLOW-012) tagged `@req REQ-FLOW-010`, `@req REQ-FLOW-012`; verify by typecheck and `uv run specworks cycle --change add-inspect-skill --json`

## 3. Writing inspection findings and suggestions

- [x] 3.1 Add the `suggestion` and `lang` parameters of `add_finding`, and `--suggestion` and `--lang` on `finding add`, as stubs (REQ-FLOW-016, REQ-CLI-011); verify `uv run specworks finding add --help`
- [x] 3.2 [test] Write failing tests for a `question` finding added to inspection (created from its template, I1, routed to review, `confirmed in inspect:` once closed) and a `diff` suggestion holding ```` ``` ```` (the pinned `**Suggestion**:` line, a four-backtick indented fence, routed by its Proposal, read back the same; an empty one refused), tagged `@ac AC-FLOW-016.12`, `@ac AC-FLOW-016.13`; keep AC-FLOW-016.1 to 016.11 passing; verify they fail on the stubs
- [x] 3.3 [test] Write a failing CLI test for `finding add ... --artifact inspection --suggestion fix.diff --lang diff` and a missing file refused, tagged `@ac AC-CLI-011.5`; keep AC-CLI-011.1 to 011.4 passing; verify it fails on the stub
- [x] 3.4 [code] Implement the suggestion fence, `confirmed in <artifact phase>:` for inspection, and the CLI options reading the file or standard input (REQ-FLOW-016, REQ-CLI-011) tagged `@req REQ-FLOW-016`, `@req REQ-CLI-011`; verify by typecheck and adding a suggestion to a scratch change with `uv run specworks finding add ...`

## 4. A closed change: trace and inspection notes

- [x] 4.1 Add `ChangedSince`, `changed_since_close(ws, change)`, `Row.changed` in `specs/trace.py` and `require_change_or_archived` in `cli/output.py` as stubs (REQ-SPECS-018, REQ-CLI-002); verify `uv run ruff check src tests && uv run mypy`
- [x] 4.2 [test] Write failing tests for the trace of a closed change (its current tests and code), a location whose file a later commit changed marked and the others not, and no marks with a note outside git, tagged `@ac AC-SPECS-018.1`, `@ac AC-SPECS-018.2`, `@ac AC-SPECS-018.3`; keep AC-SPECS-012.1 to 012.5 passing; verify they fail on the stubs
- [x] 4.3 [test] Write failing CLI tests for `trace` of an archived change (exit 0; `--write` refused, no file changes) and inspection notes on an archived change (I1 in its archive folder; `--artifact review` refused), and update AC-CLI-002.4 for the new exceptions, tagged `@ac AC-CLI-002.8`, `@ac AC-CLI-002.9`, `@ac AC-CLI-002.4`; keep the other AC-CLI-002 criteria passing; verify the new ones fail on the stubs
- [x] 4.4 [code] Implement the close commit and the changed files from git, the marks in the trace (text and `--json`), and `trace`/`finding` reading an archived change only as REQ-CLI-002 allows (REQ-SPECS-018, REQ-CLI-002) tagged `@req REQ-SPECS-018`, `@req REQ-CLI-002`; verify by typecheck and `uv run specworks trace --change unify-check-findings --json`

## 5. The skill and its peer

- [x] 5.1 [code] Write `src/specworks/skills/specworks-inspect/SKILL.md` as design.md's seven steps with its pinned wording, read-only but for `specworks finding ... --artifact inspection` and the commit; add the harness peer `peers/inspect.py` (`InspectPeer`); have the review skill mark each `I` finding it checked `done in review:`; run `uv run specworks skills` (the harness asks one peer per skill); verify `uv run pytest tests/test_skills.py tests/harness`
- [x] 5.2 [code] Add skill wording tests to `tests/test_skills.py`: the pinned phrases of design.md, the allowed commands (read-only git, `specworks finding`, `specworks commit`), and the hand-over to `/specworks-review` or `/specworks-reopen` (no capability: untagged); verify `uv run pytest tests/test_skills.py`

## 6. Removed criteria of a closed change (reopened: inspection.md I1)

- [ ] 6.1 Add `living_spec_at(ws, change, cap, commit)` in `specs/trace.py` as a stub per design.md Interfaces (REQ-SPECS-018); verify `uv run ruff check src tests && uv run mypy`
- [ ] 6.2 [test] Write failing tests for a criterion added after the close (not removed) next to one the change left out and still tagged (still removed), and for no close commit (nothing removed), tagged `@ac AC-SPECS-018.4`, `@ac AC-SPECS-018.5`; keep AC-SPECS-018.1 to 018.3 passing; verify they fail on the stub
- [ ] 6.3 [code] Implement the living spec at the close commit and `dropped_criteria` compared with it for an archived change, none without the commit (REQ-SPECS-018) tagged `@req REQ-SPECS-018`; verify by typecheck and `uv run specworks trace --change unify-check-findings --json` showing no removedStillTagged

## Workflow follow-up

- `unify-check-findings` left four clean-ups for a `fix-` change: validate described as read-only in the done and onboard skills, `DECISION_FORM` not naming `back to review:`, the private `_new_artifact` import, and `1 warnings` in the validation Summary.
