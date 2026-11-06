# Review: add-chatinho-harness

Base: `b6e39e6` (`main` and `origin/main` are both stale at #92 in this checkout, so every `specworks review` and `gate review` here runs with `--base b6e39e6`, the merge of #111 the branch started from)

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **design-gap** AC-HARNESS-006.1 fails on Python 3.12 (tests/harness/test_workspaces.py:45): a peer that runs run_workspace and then write_file in the same run writes into the main checkout, not the workspace. SkillPeer.graph() (src/specworks/harness/peers.py:94-104) picks the Deep Agent's backend, confined(root), once per run from the peer's workspace at the start of the run, so the /workspace switch only takes effect on the next run. design.md's Decision 'caches the graph per (chat shape, workspace)' with backend=confined(workspace) is what proved wrong; deepagents 0.7 removed backend factories, so the backend must itself follow the peer's workspace (REQ-HARNESS-006, REQ-HARNESS-008)
  - **Proposal**: back to design: give the Deep Agent one backend per peer that resolves Workspaces.path_of(peer) at every file or shell call (e.g. a delegating backend in confine.py over confined(<current workspace>)), cache the graph per chat shape only, and update the SkillPeer Decision and the confine.py Interfaces; then the code half implements it; the existing test already covers it
  - **Decision**: back to design: each peer gets one backend that looks up Workspaces.path_of(peer) on every file or shell call; cache the graph per chat shape only
- [ ] R2 **code-gap** AC-HARNESS-008.1 fails on Python 3.12 (4 cases in tests/harness/test_confine.py): reading or writing ../outside.txt or an absolute path outside the workspace raises ValueError out of ConfinedShell.read/write instead of returning an error result. deepagents' read/write catch only OSError/RuntimeError around _resolve_path, and ConfinedShell._resolve_path (src/specworks/harness/confine.py:29-44) raises ValueError; at the agent level an absolute path outside passes the tool's validate_path, so the exception fails the whole run instead of being an error the agent sees (REQ-HARNESS-008: 'A refusal SHALL be an error the agent sees')
  - **Proposal**: back to code: make ConfinedShell return the backend's error result (ReadResult/WriteResult/EditResult etc. with error set, nothing read or written) for a path outside the workspace instead of letting ValueError escape, for every file operation that resolves a path
  - **Decision**: back to code: ConfinedShell returns error results for paths outside the workspace and changes nothing
- [ ] R3 **quality** The model key leaks to the shell: ConfinedShell passes inherit_env=True (src/specworks/harness/confine.py:27), so every peer's shell gets SPECWORKS_MODEL_API_KEY; 'env | grep SPECWORKS_MODEL' run through confined(root).execute prints 'SPECWORKS_MODEL_API_KEY=sk-secret', which then goes into the model's context, replies and chat.jsonl. Breaks REQ-HARNESS-010 ('A key's value SHALL never appear in any output, error, file or message'); AC-HARNESS-010.3's tests only cover a failing model
  - **Proposal**: back to implement: code: build the shell's environment from os.environ without the SPECWORKS_MODEL_* variables (and the SPECWORKS_LANGFUSE_* keys) and pass it with inherit_env=False; test: add a case under AC-HARNESS-010.3 that runs 'env' through confined(root).execute with SPECWORKS_MODEL_API_KEY=sk-secret set and asserts sk-secret is not in the output
  - **Decision**: back to implement: strip SPECWORKS_MODEL_* and SPECWORKS_LANGFUSE_* from the shell's environment (code); add a case under AC-HARNESS-010.3 that env in a peer's shell holds no key (test)
- [ ] R4 **quality** PUSH_RE = r'\bgit\b.*\bpush\b' (src/specworks/harness/confine.py:11, pinned in design.md Interfaces) refuses more than a git push: 'git stash push -m wip' and 'git commit -m "push later"' are both refused (checked with refuses()), so a peer cannot stash or write a commit message that mentions push. REQ-HARNESS-008 asks to refuse a git push command only
  - **Proposal**: back to design: change PUSH_RE in design.md Interfaces to match git followed by optional global options and then the push subcommand (e.g. r'\bgit(\s+-{1,2}\S+(\s+[^-\s]\S*)?)*\s+push\b', so 'git -C x push' is still refused), then the code half updates it and the test half adds 'git stash push' and a commit message mentioning push to the commands that run under AC-HARNESS-008.3
  - **Decision**: back to design: match only git's push subcommand (global options allowed); code updates PUSH_RE, tests add git stash push and a commit message mentioning push
- [x] R5 **spec-gap** Workspaces.merge refuses a workspace with uncommitted changes ('workspace <name> has uncommitted changes: commit them in it before merging', src/specworks/harness/workspaces.py:101); no requirement of REQ-HARNESS-007 describes this refusal and no test covers it. It guards real data: after a merge, 'git worktree remove' would fail on a dirty worktree (or the uncommitted work would be left behind)
  - **Proposal**: accepted: a guard that keeps uncommitted work in the workspace and keeps the merge from half-finishing; it adds no feature (alternative: back to specify to add a scenario to REQ-HARNESS-007 with its test)
  - **Decision**: accepted: a guard that keeps uncommitted work and stops the merge half-finishing; it adds no feature

## Changed files without tags

- `src/specworks/harness/__init__.py`: re-exports only (`build_harness`, `run_harness`, `model_from_env`, `ModelSettingsError`), tagged where they are defined (REQ-HARNESS-001, REQ-HARNESS-010, REQ-CLI-022).
- `tests/harness/conftest.py`: test fixtures and the skip of the folder without the harness extra (task 1.4); no criterion of its own.
- `tests/harness/scripted.py`: the scripted chat model and chat helpers the tagged harness tests use (task 1.4, REQ-HARNESS-002); no criterion of its own.

## Summary

Every requirement has code and every criterion a test, and the full suite passes on the project's Python 3.11, but there `tests/harness` is not even collected and the 3 harness CLI tests skip: on Python 3.12 with the extra (as CI's 3.12+ jobs run it), 5 harness tests fail (R1: a /workspace switch does not move the file tools within the run; R2: refusals outside the workspace raise instead of returning an error). Reading the code found the model key reaching every peer's shell environment (R3), an over-broad `git push` pattern (R4) and an unspecified uncommitted-changes guard on merge (R5). Nothing was fixed here (inside /specworks-build): R1 and R4 go back to design, R2 to code, R3 to both halves; R5 is proposed as accepted.
