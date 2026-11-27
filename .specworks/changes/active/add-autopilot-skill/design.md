# Design: add-autopilot-skill

## Context

See `proposal.md`. Skills are Markdown with frontmatter in
`src/specworks/skills/specworks-*/SKILL.md`, shared text pulled in with
`<!-- specworks:include <name> -->`. `/specworks-build` and
`/specworks-done` are coordinators (`_shared/phase-subagents.md`): every
phase runs in a subagent with a fixed prompt and returns `Result: done`,
`Result: question` or `Result: blocked`; the coordinator asks the user and
writes the answer to disk. The harness builds one peer per packaged skill
(`src/specworks/harness/peers/`); only `build` gets `MERGE_RULE`, because
only the user merges (REQ-HARNESS-004).

## Goals / Non-Goals

**Goals:**
- One coordinator skill that runs a change from its current phase to a
  passed validate, answering the routine stops itself and logging every
  decision, then stops before close with the hard ones to validate.
- Reuse the build and done coordinators rather than restate them.

**Non-Goals:**
- A persistent mode, a CLI command or a schema artifact.
- Running close, pushing, or touching refinement.

## Decisions

### Autopilot is the user at the coordinator's stops, nothing more

Autopilot chains the phases as the coordinators do: specify (when the
change is in specify) in a subagent, then `/specworks-build` followed as
its coordinator from its step 1, then validate in a subagent with the
validate line of `/specworks-done`. Wherever build, done or a subagent
would ask the user, autopilot answers by the rules below and writes the
answer where the coordinators write it. Build's report-and-stop is skipped:
autopilot goes on to validate. Alternative: restate build's cycle logic in
the autopilot skill; rejected, two copies of the cycle rules would drift.

| Phase in `specworks status` | Autopilot runs |
|---|---|
| `refine` | nothing: refuses, `/specworks-refine <ref>` or `/specworks-specify <ref>` |
| `specify` | specify, then the build, then validate |
| `design`, `implement`, `review` | the build, then validate |
| `validate` | validate |
| `close`, or a closed change | nothing: refuses, `/specworks-done <ref>` (close) |

### The answer rules

1. A question with an option marked `(recommended)`: take it.
2. A yes/no question that continues the flow (agree to the requirements,
   the API, start the next cycle): yes.
3. A question that needs free text (a reason, a command), or has no
   option to take: stop.
4. When the review of cycle 3 still has open findings: stop instead of
   starting cycle 4.

An answer that has no place in the coordinators' table (the specify
confirmation) is its entry in `autopilot.md`, which a restarted subagent
reads with the change's other artifacts.

### `autopilot.md`: one entry per decision, written when it is taken

A plain file in the change folder, written by the skill only; the phases
commit it with the change folder. Format:

```
# Autopilot: <ref>

Started in <phase> on <date>.

## D<n> <phase>: <the question, one line>

- **Options**: <the options as offered>
- **Chosen**: <the option taken>
- **Why**: <one line>
- **Hard**: yes - <why> | no
- **Undo**: <how to undo it> (hard ones only)

## Stop: <reason>
```

A decision is hard when its options were close, when it settles product
intent or an API, or when it is costly to undo. A second cycle and every
later one is hard. Alternative: declared in `schema.yaml`; rejected by the
user (proposal, Out of Scope).

### The report

At the stop: the reason, then `Decisions to validate` (the hard ones, each
with its undo), then `Also taken` (the rest, one line each), read from
`autopilot.md`. When validate passed the closing question recommends
`/specworks-done <ref>`; otherwise the skill the stop points to.

### The harness peer merges through the user (REQ-HARNESS-004)

`AutopilotPeer` gets `rules = (MERGE_RULE,)` like `BuildPeer`, since its
skill merges the test half's worktree. Alternative: no rule (it would merge
behind the user) or handing over to build (autopilot would do nothing in the
harness); both rejected with the user.

### Pinned wording

The test half asserts these and the code half writes them, verbatim (line
wraps folded):

- `specworks-autopilot/SKILL.md`:
  - frontmatter `name: specworks-autopilot`; the `description` contains
    `autopilot`, `(recommended)`, `before close` and
    `"specworks autopilot"`;
  - `allowed-tools` is exactly the one of `specworks-build` (with `Agent`);
  - includes `running-cli`, `asking-the-user`, `picking-the-change` and
    `phase-subagents`;
  - `**Phases in subagents**` (from the include) and the three `Result:`
    lines;
  - `Autopilot never runs in refine: refinement stays with the user.`
  - `Autopilot never runs close and never pushes.`
  - `follow ../specworks-build/SKILL.md as its coordinator`
  - `take the option marked (recommended)`
  - `A yes/no question that continues the flow is answered yes.`
  - `A question that needs free text, or has no option to take, stops autopilot.`
  - `When the review of cycle 3 still has open findings, stop instead of starting cycle 4.`
  - `A decision is hard when its options were close, when it settles product intent or an API, or when it is costly to undo.`
  - `## D<n> <phase>: <the question, one line>` and `- **Hard**: yes - <why> | no`
  - `Decisions to validate` and `Also taken`
  - `1. /specworks-done <ref> (recommended): validate passed; close it once you agree with the decisions`
  - `End with the report of step 4 of the skill before the Result line: PASS is Result: done, FAIL is Result: blocked.`
- `specworks-refine/SKILL.md`, step 5's closing options, in this order:
  `1. /specworks-specify <ref> (recommended): write the proposal, specs and tasks`,
  `2. /specworks-autopilot <ref>: specify, build and validate on their own, stopping before close`,
  `3. Stop here`.
- `specworks-onboard/SKILL.md`, the primer's flow bullet:
  `` `/specworks-autopilot` runs from specify to validate on its own, taking the recommended option at each stop, and stops before close with the hard decisions to validate. ``

The existing `test_only_build_and_done_run_their_phases_in_subagents`
(`tests/test_skills.py`) names the coordinators; autopilot joins them.

## Interfaces

- `src/specworks/harness/peers/autopilot.py`: `AutopilotPeer(SkillPeer)`,
  `@connector("autopilot")`, `rules = (MERGE_RULE,)` (REQ-HARNESS-001,
  REQ-HARNESS-004).
- `src/specworks/harness/peers/__init__.py`: `PEERS` gains `AutopilotPeer`,
  after `AdoptPeer` (alphabetical order of name).
- `src/specworks/skills/specworks-autopilot/SKILL.md`: the skill
  (`/specworks-autopilot <ref>`).

## Diagrams

No structural change: the new peer is one more module of the harness's
`peers/` package, which its block diagram shows as a whole, and the skill is
packaged data.

## Risks / Trade-offs

- [autopilot accepts a wrong recommendation] -> every decision is logged
  when taken, hard ones first in the report, and close stays with the user.
- [a loop of review findings] -> the cycle 3 stop.
- [the coordinator's context grows over a long run] -> phases run in
  subagents, and a rerun resumes from the phase and `autopilot.md`.

## Open Questions

None.
