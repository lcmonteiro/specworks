# Review: split-harness-peers

Base: `origin/main`

## Findings

- [ ] R1 **test-gap** AC-HARNESS-006.1/006.2: test_ac_harness_006_1_an_explicit_worktree_set passes worktrees={'test'}, the same set as the default worktree_peers(), so it still passes if SpecworksWorktrees ignores its worktrees argument (tests/harness/test_workspaces.py:93)
  - **Proposal**: back to test: build the provider with a set other than the default (e.g. worktrees=frozenset() so test gets the main checkout, or {'refine'} so refine gets a worktree) and assert provision follows that set

## Changed files without tags

- `src/specworks/harness/peers/adopt.py`: declaration only, the `adopt` kind of REQ-HARNESS-001; traced through `PEERS` (`peers/__init__.py`, `@req REQ-HARNESS-001`) and AC-HARNESS-001.3/001.4
- `src/specworks/harness/peers/baseline.py`: declaration only, the `baseline` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/close.py`: declaration only, the `close` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/code.py`: declaration only, the `code` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/design.py`: declaration only, the `design` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/done.py`: declaration only, the `done` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/onboard.py`: declaration only, the `onboard` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/refine.py`: declaration only, the `refine` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/reopen.py`: declaration only, the `reopen` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/review.py`: declaration only, the `review` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/specify.py`: declaration only, the `specify` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/start.py`: declaration only, the `start` kind of REQ-HARNESS-001; traced through `PEERS`
- `src/specworks/harness/peers/validate.py`: declaration only, the `validate` kind of REQ-HARNESS-001; traced through `PEERS`

## Summary

The split matches the delta specs and design.md: the `peers/` package, the 15
`<Name>Peer` classes, `PEERS`, `worktree_peers()`, the five-line `PREAMBLE` with
`MERGE_RULE` only for `build`, and `SpecworksWorktrees(ws, worktrees)` reading
`self.worktrees`; no `WORKTREE_PEERS` is left. The suite passes (1134 tests).
One test-gap: the explicit-`worktrees` test passes the default set, so it would
not catch the provider ignoring the argument (R1, proposed back to test).
