# Proposal: split-harness-peers

## Why

Every harness step runs as one shared peer class, so what is special about a
step lives elsewhere (the `test` worktree rule in the workspace provider, the
`/merge` rule in the preamble every peer gets, though only `build`
merges a worktree's branch). Giving each step its own peer, in its own file, puts a step's specifics
in one place and stops sending steps text that is not theirs.

## What Changes

- The harness peers become one kind of peer per packaged skill, each defined in
  its own module under the harness's peers package, on a shared base.
- Each step's peer states what is special about it: the `test` peer asks for its
  own worktree; the `build` peer adds the rule to ask the user to run
  `/merge <name>`.
- The preamble every peer gets keeps the rules common to all steps; the
  `/merge` rule goes only to `build`, the one skill that merges a worktree's
  branch (`done` merges specs at close, not a branch).
- The set of peer kinds and the set of packaged skills must match one to one.
- The chat otherwise behaves as today: same peer names, tools, hand-overs,
  workspaces and unchanged skills.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `harness`: REQ-HARNESS-001 (one peer per skill: its own kind and module, and
  the match with the skills) and REQ-HARNESS-004 (the `/merge` rule only for `build`,
  the peer whose skill merges a worktree's branch).

## Related requirements

- REQ-HARNESS-001 modified
- REQ-HARNESS-004 modified
- REQ-HARNESS-002 left: tools, memory and the agent run are the same for every peer
- REQ-HARNESS-006 left: which peer works in a worktree does not change, only where it is stated
- REQ-HARNESS-007 left: the `/merge` command itself does not change
- REQ-FLOW-015 left: merging a half's branch is unchanged
- REQ-CLI-010 left: `specworks merge` is unchanged
- REQ-PROJ-013, REQ-SPECS-006, REQ-SPECS-013, REQ-SPECS-015, REQ-SPECS-017, REQ-FLOW-009, REQ-CLI-007, REQ-CLI-017 left: matched only on the word "merge" or "preamble"; unrelated to harness peers

## Impact

- `src/specworks/harness/peers.py` becomes the package `src/specworks/harness/peers/`
  (a base module plus one module per skill and the list of peers).
- `src/specworks/harness/session.py` builds the listed peers.
- `src/specworks/harness/workspaces.py` takes which peers get a worktree from the
  peers instead of `WORKTREE_PEERS`.
- `tests/harness/test_peers.py` and `test_workspaces.py` follow the new layout.
- No new dependency; the packaged skills are untouched.

## Out of Scope

- Changing any skill's text.
- Giving any step its own model, memory or new tools now (the classes allow it later).
- Changing which peers get a worktree, or how `/merge` works.
