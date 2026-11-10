# Tasks: split-harness-peers

## 1. One class and file per step

- [ ] 1.1 Turn `peers.py` into the package `src/specworks/harness/peers/` per design.md Interfaces: `base.py` (the current contents, `MERGE_RULE`, `worktree`, `rules`, `skill_name()`, `__init__(model, peers)`), the 15 `<name>.py` modules with their `<Name>Peer` stubs, and `__init__.py` with `PEERS` and `worktree_peers()` as stubs (REQ-HARNESS-001); verify `uv run ruff check src tests && uv run mypy`
- [ ] 1.2 [test] Write failing tests that every peer is of its own class, defined in the peers package's module named after it, and that `PEERS` matches `packaged_skills()` one to one, tagged `@ac AC-HARNESS-001.3`, `@ac AC-HARNESS-001.4`; move the existing peer tests to build peers from `PEERS` and keep AC-HARNESS-001.1 and 001.2 passing; verify the new ones fail on the stubs
- [ ] 1.3 [code] Implement the base, the 15 step classes, `PEERS` and `build_harness` building one peer per class (REQ-HARNESS-001) tagged `@req REQ-HARNESS-001`; verify by typecheck and `uv run python -c "from specworks.harness.peers import PEERS; print([c.name for c in PEERS])"` on Python 3.12+

## 2. The merge rule only for build

- [ ] 2.1 Add `MERGE_RULE` and the `rules` parameter of `preamble` and `skill_instructions` as stubs (REQ-HARNESS-004); verify `uv run mypy`
- [ ] 2.2 [test] Update the pinned `PREAMBLE` test to the five common lines and add a test that only `build`'s preamble holds `MERGE_RULE` and no other peer's preamble mentions `/merge`, tagged `@ac AC-HARNESS-004.1`, `@ac AC-HARNESS-004.3`; keep AC-HARNESS-004.2 passing; verify the new ones fail on the stubs
- [ ] 2.3 [code] Implement the five-line `PREAMBLE`, `MERGE_RULE` and `rules` appended by `preamble`, with `BuildPeer.rules = (MERGE_RULE,)` (REQ-HARNESS-004) tagged `@req REQ-HARNESS-004`; verify by printing `preamble("build", ...)` and `preamble("done", ...)`

## 3. The worktree stated by the test peer

- [ ] 3.1 Add `SpecworksWorktrees(ws, worktrees=None)` and remove `WORKTREE_PEERS` as stubs (REQ-HARNESS-006); verify `uv run mypy`
- [ ] 3.2 [test] Keep the workspace tests of AC-HARNESS-006.1 to 006.5 passing with the provider built from `worktree_peers()` and with an explicit `worktrees` set, tagged `@ac AC-HARNESS-006.1`, `@ac AC-HARNESS-006.2`; verify they pass once the code half lands and fail now only where the stubs are reached
- [ ] 3.3 [code] Implement `worktree_peers()`, `TestPeer.worktree = True` and the provider reading `self.worktrees`, with `build_harness` passing `worktree_peers(PEERS)` (REQ-HARNESS-006) tagged `@req REQ-HARNESS-006`; verify by typecheck and a grep that no `WORKTREE_PEERS` is left in `src`

## Workflow follow-up

- The living harness design (module list, the SkillPeer decision, WORKTREE_PEERS) is rewritten by close from this change's design.md.
