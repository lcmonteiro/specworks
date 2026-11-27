# Refinement: add-autopilot-skill

## Problem

Once a change is refined, taking it through specify, design, implement,
review and validate means answering every stop by hand, even when the
`(recommended)` option is plainly the one to take. The person running the
flow has to stay at the keyboard for decisions they would accept anyway,
and the decisions that really need them are buried among the routine ones.

## Outcomes

- `/specworks-autopilot <ref>` can be entered on a change in any phase after
  refine (specify, design, implement, review, validate) and runs the rest
  of the flow without stopping for routine decisions.
- At every stop it takes the `(recommended)` option; a yes/no question that
  continues the flow is answered yes; a question that needs free text (a
  reason, a command) stops it and is asked of the user.
- It stops before close: when validate passes, or earlier when a phase is
  blocked, a question has no default, or 3 build cycles still leave open
  findings.
- When it stops, it reports the hardest decisions it took for the user to
  validate first, then the rest in one line each, all read from
  `autopilot.md` in the change folder.
- It is never on in refine (it refuses a change still in refine) and never
  runs close, so it is off once the change is closed.
- The end of `/specworks-refine` offers autopilot as an option beside the
  manual `/specworks-specify`, which stays recommended.

## Context

**Observed:**
- `/specworks-build` and `/specworks-done` are coordinators: each phase runs
  in a fresh subagent with a fixed prompt, and every `Result: question` is
  asked of the user and its answer written to disk
  (`src/specworks/skills/_shared/phase-subagents.md`).
- Every skill stop ends with one closing question: yes/no, or numbered
  options with exactly one `(recommended)`
  (`src/specworks/skills/_shared/asking-the-user.md`), so a recommended
  option is machine-findable.
- The harness already auto-takes the recommended option, but only for a
  question that offers the next step (`PREAMBLE` in
  `src/specworks/harness/peers/base.py`); anything else goes to `ask_user`.
- REQ-HARNESS-001 requires exactly one harness peer kind, in its own module,
  per packaged skill (AC-HARNESS-001.4), so a new skill needs a peer kind.
- `/specworks-build` asks `Start cycle N: ...? (yes/no)` after a review with
  findings; this repository's longest build so far took 3 cycles
  (pr-review-with-inspect).
- `tests/test_skills.py` checks some skill wording verbatim.

**Assumed:**
- A coordinator can read the current phase from `specworks status` and
  pick the next phase skill from it, as `/specworks-onboard` does.
- A subagent's `Result: question` always carries its options, so the
  coordinator can answer it without seeing the phase's conversation.

## Constraints

- [hard] Autopilot never runs close, never pushes, and never runs in the
  refine phase.
- [hard] Every decision it takes is written to disk (`autopilot.md`) when it
  is taken, so it survives subagents, `/compact` and new sessions.
- [hard] Each phase is still done exactly as its own skill says; autopilot
  only answers the stops, it skips no check and adds no gate.
- [hard] Skills are edited in `src/specworks/skills/` and refreshed with
  `uv run specworks skills`.
- [soft] No CLI change; reuse the coordinator pattern of build and done.

## Options

### Option A: a coordinator skill

`/specworks-autopilot <ref>` reads the phase from `specworks status`,
refuses refine, and chains the remaining phases with the subagent pattern
build and done use, stopping before close. It answers each
`Result: question` itself: the `(recommended)` option, yes for a yes/no that
continues the flow, a stop for free text or after 3 open-finding cycles.
Each answer goes where the phase reads it and is logged in `autopilot.md`
(phase, question, options, chosen, why, hard or not with the reason: close
options, product intent or API, costly to undo). Resuming is running it
again.

- **Pros:** no CLI change; one place holds the whole behaviour; off after
  close by construction.
- **Cons:** a phase skill run on its own is never on autopilot.
- **Effort:** M
- **Touches:** a new skill, `harness` (peer kind), `specworks-refine` text
- **Outcomes:** meets all.

### Option B: a mode flag on the change

`specworks autopilot on|off --change` stores the mode in the change's state;
`status` shows it, every phase skill reads it and answers its own stops,
close clears it and refine refuses it.

- **Pros:** works with each phase skill run on its own.
- **Cons:** a CLI command, workflow state, `status` output and a shared rule
  in every phase skill: one feature spread over the whole surface.
- **Effort:** L
- **Touches:** `cli`, `workflow`, `project`, every phase skill, `harness`
- **Outcomes:** meets all, and a single phase on autopilot besides.

### Option C: harness only

Extend the harness preamble rule to every recommended option.

- **Pros:** smallest change.
- **Cons:** does nothing in Claude Code or Copilot, where most runs happen.
- **Effort:** S
- **Touches:** `harness`
- **Outcomes:** fails the first (entering autopilot outside the harness).

## Recommendation

Option A, agreed with the user: it meets every outcome with no CLI change,
and stopping before close is built into what the skill chains rather than a
flag someone must clear.

## Open Questions

- Is `autopilot.md` declared in `schema.yaml` (template, `instructions`) or
  a plain file the skill writes? (who can answer: specify, with the user)
- Should `/specworks-onboard` and `/specworks-build` mention autopilot?
  (who can answer: specify, with the user)

## Candidate Capabilities

- `harness`: modified - a peer kind `autopilot` for the new
  `specworks-autopilot` skill (REQ-HARNESS-001).
- `workflow`: modified only if `autopilot.md` becomes a declared artifact.
- Skills (no capability): a new `specworks-autopilot` skill, and the closing
  question of `specworks-refine`.
