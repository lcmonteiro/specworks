# Tasks: add-autopilot-skill

## 1. The harness peer

- [x] 1.1 Add `AutopilotPeer` in `src/specworks/harness/peers/autopilot.py` with `rules = (MERGE_RULE,)`, and add it to `PEERS` after `AdoptPeer`, with a stub `src/specworks/skills/specworks-autopilot/SKILL.md` (frontmatter only) so the peer has its skill (REQ-HARNESS-004, REQ-HARNESS-001); verify `uv run specworks run lint` passes
- [x] 1.2 [test] Update `test_ac_harness_004_3_the_merge_rule` in `tests/harness/test_peers.py`, tagged `@ac AC-HARNESS-004.3`: `build` and `autopilot` get `MERGE_RULE`, no other peer mentions `/merge`; verify it fails before 1.3
- [ ] 1.3 [code] Tag `AutopilotPeer` with `@req REQ-HARNESS-004` and `REQ-HARNESS-001` in its docstring as `BuildPeer` does (REQ-HARNESS-004); verify `uv run specworks run lint` passes

## 2. The autopilot skill

- [x] 2.1 [test] Add untagged wording checks to `tests/test_skills.py` for `specworks-autopilot`: every phrase under **Pinned wording** in design.md for that skill, `allowed-tools` equal to build's, the four includes; and add `specworks-autopilot` to the coordinators of `test_only_build_and_done_run_their_phases_in_subagents` (AC-HARNESS-004.3: the skill merges, so it is a coordinator); verify they fail before 2.2
- [ ] 2.2 [code] Write `src/specworks/skills/specworks-autopilot/SKILL.md`: frontmatter, boundary, the phase table, the answer rules, `autopilot.md` and its format, the stops, the report and the closing question, all with the pinned wording (REQ-HARNESS-004: it merges like build); verify by reading it against design.md

## 3. Refine and onboard

- [x] 3.1 [test] Add untagged checks to `tests/test_skills.py` for refine's three closing options in order and onboard's autopilot line, from **Pinned wording** (AC-HARNESS-004.3: autopilot is offered where the flow continues); verify they fail before 3.2
- [ ] 3.2 [code] Write refine's step 5 closing options and onboard's primer line with the pinned wording (REQ-HARNESS-004); verify by reading both skills
- [ ] 3.3 [code] Refresh the installed copies with `uv run specworks skills` and run `uv run specworks run lint` (REQ-HARNESS-001); verify `.claude/skills/specworks-autopilot/SKILL.md` exists and lint passes
