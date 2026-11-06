# Tasks: add-chatinho-harness

## 1. Packaging and the change's .gitignore

- [x] 1.1 Add the `harness` extra and dev entries (chatinho pinned, deepagents; Python >= 3.12 markers), the mypy override, the `src/specworks/harness/` package with its modules as stubs per design.md Interfaces, `ensure_ignored` in `src/specworks/core/events.py` and `src/specworks/cli/harness.py` as stubs (REQ-HARNESS-001, REQ-CLI-022, REQ-PROJ-030); verify `uv sync`, `uv run ruff check src tests && uv run mypy` and `uv run specworks --help` pass
- [x] 1.2 [test] Write failing tests in `tests/project/` for an existing `.gitignore` gaining the missing names once, tagged `@ac AC-PROJ-030.6`; keep the tests of AC-PROJ-030.1 to AC-PROJ-030.5 passing; verify the new test fails on the stub
- [ ] 1.3 [code] Implement `ensure_ignored` and call it from `record_event` (REQ-PROJ-030) tagged `@req REQ-PROJ-030`; verify by lint and typecheck, and a manual `record_event` on a folder whose `.gitignore` names `chat.jsonl`
- [x] 1.4 Add `tests/harness/conftest.py` (skip the folder when chatinho or deepagents cannot be imported) and the scripted chat model `tests/harness/scripted.py` (tests only, no network) (REQ-HARNESS-002); verify `uv run pytest tests/harness` collects on 3.12+ and skips on 3.11

## 2. The model from the environment

- [x] 2.1 [test] Write failing tests for reading the three variables, a missing key or model, and a key that never appears in replies, logs or `chat.jsonl`, tagged `@ac AC-HARNESS-010.1`, `@ac AC-HARNESS-010.2`, `@ac AC-HARNESS-010.3`; verify they fail on the stubs
- [ ] 2.2 [code] Implement `model_from_env` and `ModelSettingsError` (REQ-HARNESS-010) tagged `@req REQ-HARNESS-010`; verify by typecheck and by calling it with an empty environment, which names `SPECWORKS_MODEL_API_KEY`

## 3. Workspaces and confinement

- [x] 3.1 [test] Write failing tests on a temporary git repository for a new workspace, reuse, back to main and bad names, tagged `@ac AC-HARNESS-006.1`, `@ac AC-HARNESS-006.2`, `@ac AC-HARNESS-006.3`, `@ac AC-HARNESS-006.4`; verify they fail on the stubs
- [x] 3.2 [test] Write failing tests for a merged workspace, a conflict and an unknown workspace, tagged `@ac AC-HARNESS-007.1`, `@ac AC-HARNESS-007.2`, `@ac AC-HARNESS-007.3`; verify they fail on the stubs
- [x] 3.3 [test] Write failing tests for paths outside the workspace, the shell's folder and a refused `git push`, tagged `@ac AC-HARNESS-008.1`, `@ac AC-HARNESS-008.2`, `@ac AC-HARNESS-008.3`; verify they fail on the stubs
- [ ] 3.4 [code] Implement `Workspaces`, `WorkspaceCommand` and `MergeCommand` (REQ-HARNESS-006, REQ-HARNESS-007) tagged `@req REQ-HARNESS-006`, `@req REQ-HARNESS-007`; verify by typecheck and a manual `/workspace` then `/merge` on a scratch repository
- [ ] 3.5 [code] Implement `refuses` and `confined` (REQ-HARNESS-008) tagged `@req REQ-HARNESS-008`; verify by typecheck and that `refuses("git push origin main")` is true and `refuses("git status")` is false

## 4. The conversation kept

- [x] 4.1 [test] Write failing tests for appending to `chat.jsonl`, holding messages until the change exists, continuing a conversation and a log that cannot be written, tagged `@ac AC-HARNESS-009.1`, `@ac AC-HARNESS-009.2`, `@ac AC-HARNESS-009.3`, `@ac AC-HARNESS-009.4`; verify they fail on the stubs
- [ ] 4.2 [code] Implement `GitBackend`, `to_line` and `from_line` (REQ-HARNESS-009) tagged `@req REQ-HARNESS-009`; verify by typecheck and that `from_line(to_line(msg))` keeps id, sender, addressee, reply, status and text

## 5. Skill peers

- [x] 5.1 [test] Write failing tests for one peer per skill and the skill text unchanged, tagged `@ac AC-HARNESS-001.1`, `@ac AC-HARNESS-001.2`; verify they fail on the stubs
- [x] 5.2 [test] Write failing tests with the scripted model for a question answered, the tools a peer gets and a failed run, tagged `@ac AC-HARNESS-002.1`, `@ac AC-HARNESS-002.2`, `@ac AC-HARNESS-002.3`; verify they fail on the stubs
- [x] 5.3 [test] Write failing tests for a hand-over starting the next peer, a chain longer than `max_depth`, a say addressed to another peer and an unknown peer, tagged `@ac AC-HARNESS-003.1`, `@ac AC-HARNESS-003.2`, `@ac AC-HARNESS-003.3`, `@ac AC-HARNESS-003.4`; verify they fail on the stubs
- [x] 5.4 [test] Write failing tests for the pinned preamble (design.md, verbatim) and a question for the user answered before the hand-over, tagged `@ac AC-HARNESS-004.1`, `@ac AC-HARNESS-004.2`; verify they fail on the stubs
- [x] 5.5 [test] Write a failing test for the user asking `test` directly, tagged `@ac AC-HARNESS-005.1`; verify it fails on the stubs
- [ ] 5.6 [code] Implement `peer_name`, `preamble` (the pinned wording) and `skill_instructions` (REQ-HARNESS-001, REQ-HARNESS-004) tagged `@req REQ-HARNESS-001`, `@req REQ-HARNESS-004`; verify by typecheck and that `skill_instructions("specworks-test", ...)` ends with `read_skill("specworks-test")`
- [ ] 5.7 [code] Implement `SkillPeer`: the Deep Agent graph in its workspace, `hand_over` said after the run from a fresh context, `listen` doing nothing (REQ-HARNESS-002, REQ-HARNESS-003, REQ-HARNESS-005) tagged `@req REQ-HARNESS-002`, `@req REQ-HARNESS-003`, `@req REQ-HARNESS-005`; verify by typecheck and lint

## 6. The session and the command

- [x] 6.1 [test] Write failing tests for the command without the extra, without a key, the request going to `refine`, continuing a change in `design` (to `build`) and other commands not importing chatinho or deepagents, tagged `@ac AC-CLI-022.1`, `@ac AC-CLI-022.2`, `@ac AC-CLI-022.3`, `@ac AC-CLI-022.4`, `@ac AC-CLI-022.5`; verify they fail on the stubs
- [ ] 6.2 [code] Implement `first_peer`, `build_harness` and `run_harness` (REQ-HARNESS-001, REQ-CLI-022) tagged `@req REQ-HARNESS-001`, `@req REQ-CLI-022`; verify by typecheck
- [ ] 6.3 [code] Implement the `harness` command with its lazy import and errors (REQ-CLI-022) tagged `@req REQ-CLI-022`; verify `uv run specworks harness --help` and, with `SPECWORKS_MODEL_API_KEY` unset, `uv run specworks harness "x"` exits 1 naming it
- [ ] 6.4 [code] Update `.github/workflows/ci.yml`: on 3.11 report coverage with `--omit "*/specworks/harness/*"`; on 3.12+ install the extra so the harness counts (REQ-CLI-022); verify the workflow file parses and `uv run coverage report` passes locally on 3.12

## Workflow follow-up

- Document `specworks harness` and the `SPECWORKS_MODEL_*` variables in the wiki after close.
