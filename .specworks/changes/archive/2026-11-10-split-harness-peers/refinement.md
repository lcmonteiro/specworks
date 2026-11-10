# Refinement: split-harness-peers

## Problem

In the harness every step (skill) runs as the same `SkillPeer` class, built
once per packaged skill. What is special about a step lives elsewhere: the
`test` worktree rule is a name set in `workspaces.py`, and the "ask the user to
`/merge`" instruction is in the shared preamble that all 15 peers get, though
only `build` and `done` merge. To see or change how one step behaves, a
maintainer has to look in several places, and every step gets text meant for
others. Each step should be its own agent class, in its own file.

## Outcomes

- `src/specworks/harness/peers/` holds a base peer and one file and class for
  each of the 15 packaged skills; each class states what is special about its
  step (workspace, prompt additions, extra tools).
- The `test` peer still works in its own git worktree, now because its class
  says so.
- Only the `build` and `done` peers are told to ask the user to run
  `/merge <name>`; the other 13 peers' instructions no longer carry that line.
- Otherwise the chat behaves as today: the same peer names, hand-overs,
  `ask_user` stops and unchanged skills.
- A test fails when the packaged skills and the peer classes do not match
  one to one (a skill with no class, or a class with no skill).

## Context

**Observed:**
- `src/specworks/harness/peers.py`: `PREFIX`, `PREAMBLE` (6 lines, the last
  one about `/merge`), `peer_name`, `preamble`, `skill_instructions`, and
  `SkillPeer(DeepAgentConnector)` with `hand_over`, `MEMORY`, `ask_user=True`.
- `src/specworks/harness/session.py`: `build_harness` builds
  `SkillPeer(skill, model, names)` for each of `packaged_skills()`.
- `src/specworks/harness/workspaces.py`: `WORKTREE_PEERS = {"test"}` decides in
  `SpecworksWorktrees.provision` which peer gets a worktree and whether the
  main checkout is writable for its owner.
- Living docs: `src/specworks/harness/docs/` (REQ-HARNESS-001 to 010; the
  design names `peers.py` and `WORKTREE_PEERS`; the blocks diagram shows
  "peers.py (SkillPeer x 15, preamble)"). Tests in `tests/harness/test_peers.py`
  and `test_workspaces.py`.
- 15 packaged skills: refine, specify, design, test, code, review, validate,
  build, done, close, reopen, adopt, baseline, onboard, start.

**Assumed:**
- The preamble lines other than the `/merge` one apply to every step and stay
  in the base class.
- No step needs its own model or memory now; the classes allow it later.

## Constraints

- [hard] The packaged skills stay unchanged; a peer's prompt is still its
  preamble plus its skill text.
- [hard] Harness tests run on Python 3.12+ (the `harness` extra).
- [hard] Peer names and hand-over behaviour stay as they are.
- [soft] One rule for every skill: a class and file each, even when a step has
  nothing special.
- [soft] Keep the per-step files short: class attributes over overridden
  methods where possible.

## Options

### Option A: `peers/` package with an explicit list

`peers/base.py` holds `SkillPeer` (preamble, `hand_over`, memory). Each
`peers/<skill>.py` subclasses it and sets class attributes such as its skill,
whether it gets a worktree, extra preamble lines and extra tools.
`peers/__init__.py` lists the 15 classes; `build_harness` builds one of each,
and the worktree provider asks the peer classes instead of `WORKTREE_PEERS`.

- **Pros:** every peer is visible in one list; no import side effects; each
  step's specifics sit next to it.
- **Cons:** a new skill needs a line in the list too (the matching test catches
  a missed one).
- **Effort:** M
- **Touches:** `harness`
- **Outcomes:** meets all.

### Option B: self-registering classes, auto-discovered

The same files, but each class registers itself with a decorator and the
package imports every module it finds (`pkgutil`).

- **Pros:** no list to keep.
- **Cons:** registration is implicit and depends on import side effects;
  harder to read which peers exist.
- **Effort:** M
- **Touches:** `harness`
- **Outcomes:** meets all.

### Option C: one class plus a per-step settings table

Keep `SkillPeer` and add a table of per-step settings (worktree, extra lines).

- **Pros:** least code.
- **Cons:** not a class and file per step, which is the request.
- **Effort:** S
- **Touches:** `harness`
- **Outcomes:** fails the first outcome.

## Recommendation

Option A (agreed with the user): a `peers/` package with a base class, one
file and class per skill, and an explicit list guarded by a test.

## Open Questions

- None blocking. The exact class attributes (names, and whether extra tools
  are needed by any step now) are settled in design.

## Candidate Capabilities

- `harness`: modified - peers become one class per skill in `peers/`, each
  carrying its step's workspace and prompt additions; the `/merge` instruction
  goes only to `build` and `done`.
