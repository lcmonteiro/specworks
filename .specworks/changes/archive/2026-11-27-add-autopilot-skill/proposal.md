# Proposal: add-autopilot-skill

## Why

Taking a refined change through specify, design, implement, review and
validate means answering every stop by hand, even when the `(recommended)`
option is plainly the one to take. The refinement chose Option A: a
coordinator skill that answers the routine stops itself, stops before close,
and hands the user the hard decisions to validate.

## What Changes

- A new packaged skill `src/specworks/skills/specworks-autopilot/SKILL.md`
  (`/specworks-autopilot <ref>`), installed like every other skill.
  - **Where it starts**: from the phase in `specworks status`: specify runs
    `/specworks-specify`, then the build, then validate; design, implement
    and review run the build, then validate; validate runs validate alone.
    A change in refine, close or already closed is refused, with the skill
    to run instead.
  - **How it runs**: it chains the phases with the coordinator rules of
    `/specworks-build` and `/specworks-done` (each phase in its own
    subagent, the test half in its worktree), and follows
    `/specworks-build` as its coordinator. Validate runs as in
    `/specworks-done`; close never runs.
  - **How it answers**: at every `Result: question` (and every stop the
    build would ask the user) it takes the `(recommended)` option; a yes/no
    question that continues the flow is answered yes; it writes the answer
    where the phase reads it, exactly as the coordinators do.
  - **When it stops**: validate passes (ready for `/specworks-done`); a
    phase returns `Result: blocked` or validate fails; a question needs free
    text or has no default; or the review of cycle 3 still has open
    findings. It never pushes and never runs close.
  - **The decision log**: every decision is appended to `autopilot.md` in
    the change folder when it is taken (phase, question, options, the
    choice, why, and whether it is hard and why: close options, product
    intent or an API, or costly to undo), and committed with its phase.
  - **The report**: at the stop, the stop reason, then the hard decisions
    first, each with how to undo it, then the rest in one line each, and a
    closing question whose recommended option is `/specworks-done <ref>`
    when validate passed.
  - Running it again resumes: the phase and `autopilot.md` are on disk.
- `/specworks-refine` ends with `/specworks-specify <ref>` (recommended),
  then `/specworks-autopilot <ref>`, then `Stop here`.
- `/specworks-onboard`'s primer explains autopilot in a line, beside build
  and done.
- The harness gets an `autopilot` peer (REQ-HARNESS-001), and, because its
  skill merges the test half's worktree like build's, the merge rule.
- Untagged wording checks in `tests/test_skills.py`; the installed copies
  refreshed with `specworks skills`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `harness`: REQ-HARNESS-004, the merge rule goes to every peer whose skill
  merges a worktree's branch (`build` and `autopilot`), not to `build` alone.

## Related requirements

- REQ-HARNESS-004 modified: the merge rule names `build` alone, and the
  autopilot skill merges too.
- REQ-HARNESS-001 left: it already asks for one peer kind per packaged skill;
  the `autopilot` peer meets it with no change.

## Impact

- `src/specworks/skills/specworks-autopilot/SKILL.md` (new),
  `specworks-refine` and `specworks-onboard` skill text, and their copies
  under `.claude/skills/`.
- `src/specworks/harness/peers/autopilot.py` (new) and the `PEERS` list in
  `src/specworks/harness/peers/__init__.py`.
- `tests/test_skills.py`, `tests/harness/test_peers.py`.
- No CLI command, config key or artifact schema changes: `autopilot.md` is a
  plain file of the change folder that only this skill reads.

## Out of Scope

- A mode flag on the change, or autopilot for a phase skill run on its own
  (Option B of the refinement).
- Running close, pushing, or opening a pull request.
- Declaring `autopilot.md` in `schema.yaml` (a template, a `status` row).
- Mentioning autopilot in the closing questions of build and done.
- Autopilot in the refine phase: refinement stays with the user.
