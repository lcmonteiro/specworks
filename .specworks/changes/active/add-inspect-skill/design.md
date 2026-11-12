# Design: add-inspect-skill

## Context

`unify-check-findings` made findings a shared model: check artifacts are
declared in `schema.yaml` (`findings: {letter, blocks}`), read and written
by `workflow/findings.py`, gated per artifact, and gathered by
`specworks cycle`. After `done in review:` a finding is routed to validate
(`NEXT_STEP["review"]`). `specworks trace` and `specworks finding` refuse an
archived change (`require_change` in `cli/output.py`); only `status` and
`reopen` read one (`resolve_archived`). The finding writers take one-line
texts (`_one_line`). See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- A skill that walks a change, open or closed, ordered by uncertainty and
  importance, in a circle the reviewer breaks, and leaves notes as `I`
  findings only when there are any.
- Inspection findings route like the others and come back to inspect.
- `trace` of a closed change, with the locations changed since its close.
- Suggestions (multi-line) on any finding, written and read back safely.

**Non-Goals:**
- A gate on inspection, or an approval record.
- A CLI command that orders the blocks: ranking is the skill's judgement.

## Decisions

### Inspection is a third check artifact, blocking nothing

`schema.yaml` gets `inspection` (`inspection.md`, phase `inspect`,
`requires: [tasks]`, `optional: true`, `findings: {letter: I, blocks: []}`)
and a template. Its phase `inspect` is not a phase of a change (`PHASES` is
unchanged): it only names the step that confirms its findings
(`confirmed in inspect:`) and that they wait for. Nothing else in the
gates, cycle or validate needs to know about it: they already go through
`check_artifacts()` and `blocks`. Serves: REQ-FLOW-018, REQ-FLOW-001.

### After review, a finding waits for its own artifact's step

`NEXT_STEP["review"]` becomes a function of the finding's artifact:
`_next_step(done_in, design_only, artifact)` returns `artifact.phase` after
review when that is not `review` (validate for V, inspect for I), and
validate for R (unchanged). `next_cycle` treats every open finding routed to
a step that is not a build step (`validate`, `inspect`) as waiting: no cycle.
Serves: REQ-FLOW-010, REQ-FLOW-012.

### `question` is a type routed to review

`TYPE_PHASE["question"] = "review"`. It is valid in any check artifact, so a
review or validate finding may be a question too; the inspect skill is the
one that uses it. `back to review:` already exists. Serves: REQ-FLOW-010.

### Suggestions are an indented fence under the finding

`add_finding(..., suggestion="", lang="text")` writes, after the Proposal
line, `  - **Suggestion**:` and then the text in a fence indented by four
spaces, with a fence of `max(3, longest backtick run + 1)` backticks and the
language after it. The reader already keeps an indented fence inside the
finding's block and ignores what is in it (AC-FLOW-010.4), so a suggestion
never routes; the write is read back as every write is. Only `add` writes a
suggestion: a later one is a new finding or a hand edit. Serves:
REQ-FLOW-016, REQ-CLI-011.

**Pinned wording**:
- `  - **Suggestion**:` (the line before the fence)
- `confirmed in inspect: ` (the close of an `I` finding)

### A closed change is read where it is archived

`cli/output.py` gets `require_change_or_archived(ref, as_json)`, used by
`trace` (refusing `--write` for an archived change) and by `finding` (only
when the artifact is `inspection`, by `--artifact` or by the ID's letter).
Every other command keeps `require_change`. The archived folder is a
`Change` like an active one, so `Analysis`, the trace and the finding
writers need nothing new to read or write it. Serves: REQ-CLI-002.

### What changed since the close comes from git

`changed_since_close(ws, change) -> ChangedSince` in `specs/trace.py`:
the close commit is the last commit that added the change's archive folder
(`git log -1 --diff-filter=A --format=%H -- <archive folder>`); the files
changed since are `git diff --name-only <commit>` (committed and
uncommitted). Without git or without that commit, `ChangedSince(None,
note)`. The trace marks a test or code location (`file:line`) whose file is
in that set: `Row.changed` lists them; the text output adds ` (changed since
close)` after each; `--json` adds `"changedSinceClose": {"commit": ...,
"files": [...]}` or `{"note": ...}`. Only for an archived change; an active
one has neither. Serves: REQ-SPECS-018.

### A closed change's removed criteria come from the spec at its close

Reopened for inspection.md I1: the trace of a closed change compared its
MODIFIED blocks with today's living spec, so every criterion a later change
added showed as removed but still tagged. For an archived change,
`dropped_criteria` now compares with the living spec as it was at the close
commit (the one `changed_since_close` finds), read with
`git show <commit>:<living spec>`: a criterion the change itself left out
and still tagged is still reported; one added later is not. Without that
commit (no git, history rewritten) no criterion is reported as removed,
rather than guessing from today's spec. Skipping the check for every
closed change was rejected: it would hide real leftover tags. Serves:
REQ-SPECS-018.

### The skill orders, the reviewer breaks the circle

`specworks-inspect` (read-only but for inspection.md, like onboard plus
`finding`):
1. Pick the change, active or archived (`status` reads both); run
   `specworks trace --change <ref> --json`.
2. Show why (proposal.md, three or four lines).
3. Build the blocks: one per scenario (a `skip-specs` change: one per task,
   with the part of the diff that carries it out), plus a block for a doubt
   that spans several. Rank them by uncertainty, then importance, and say
   the rank's reason in one line per step.
4. Each step: WHEN and the code, THEN and the test, each cut to the lines
   that matter with `file:line` (and `changed since close`), the design
   excerpt that argues for it, at most three one-line hints, then the
   options: next block (recommended), add a note, show more, come back
   later, jump to a requirement, stop here.
5. A note becomes a finding: `specworks finding add <type> "<text>"
   --proposal "back to <step>: ..." --artifact inspection [--suggestion -
   --lang <lang>]`. On a later inspection, its open `I` findings routed to
   inspect are shown first and closed once confirmed.
6. After the last block, the deferred ones, until none is left or the
   reviewer stops. Stopping is a normal end.
7. End: blocks walked out of total, notes written. No notes: nothing is
   written. With notes: commit inspection.md, then `/specworks-review`
   (open change) or `/specworks-reopen` with inspection.md as the problem
   (closed change).

**Pinned wording** (skill text, checked by `tests/test_skills.py`):
`come back later`, `stop here`, `most uncertain and important first`,
`at most three hints`, `No notes: nothing is written`.

## Interfaces

Agreed with the user

- `src/specworks/schema.yaml`: artifact `inspection` (`inspection.md`,
  phase `inspect`, template `inspection.md`, `requires: [tasks]`,
  `optional: true`, `findings: {letter: I, blocks: []}`) (REQ-FLOW-018,
  REQ-FLOW-001)
- `src/specworks/templates/inspection.md`: `# Inspection: <!-- change ref -->`,
  `## Findings` (guidance comment), `## Summary` (blocks walked of total)
- `src/specworks/workflow/findings.py`: `TYPE_PHASE` gains `question:
  review`; `_next_step(done_in, design_only=False, artifact: CheckArtifact | None = None)`
  (`None`: validate after review, as today);
  `add_finding(change, kind, text, proposal, artifact="review", check="",
  suggestion: str | None = None, lang="text") -> Finding` (`None`: no
  suggestion; an empty `suggestion`, `""` or blank, raises `FindingError`.
  The default is `None`, not `""`, so that an explicit empty one can be
  told apart from none) (REQ-FLOW-010, REQ-FLOW-016)
- `src/specworks/workflow/cycle.py`: `WAITING_STEPS = ("validate",
  "inspect")`; `next_cycle` leaves findings routed there out of the cycle
  (REQ-FLOW-012)
- `src/specworks/specs/trace.py`: `living_spec_at(ws: Workspace, change: Change,
  cap: CapabilityRef, commit: str | None) -> str | None` (the capability's
  living spec text at that commit, by `git show`; None without the commit,
  without git, or when the spec did not exist then; it raises nothing). It
  is the only new interface: `Analysis.rows` comparing an archived change
  with it is the code half's (REQ-SPECS-018);
  `src/specworks/specs/trace.py`: `ChangedSince(commit: str | None, files:
  frozenset[str], note: str = "")`; `changed_since_close(ws, change) ->
  ChangedSince`; `Row.changed: list[str]` (REQ-SPECS-018)
- `src/specworks/cli/output.py`: `require_change_or_archived(ref, as_json)
  -> tuple[Workspace, Module, Change]` (REQ-CLI-002)
- `src/specworks/cli/specs.py`: `trace` reads an archived change, refuses
  `--write` for one, prints `changedSinceClose` (REQ-CLI-002, REQ-SPECS-018)
- `src/specworks/cli/workflow.py`: `finding add ... --suggestion <file|->
  --lang <language>`; `finding` on an archived change only for inspection
  (REQ-CLI-011, REQ-CLI-002)
- `src/specworks/skills/specworks-inspect/SKILL.md` (new);
  `src/specworks/harness/peers/inspect.py`: `InspectPeer` (REQ-HARNESS-001,
  already required for every packaged skill)

## Diagrams

No structural change: the new peer is one more module of the harness's
`peers/` package, which its block diagram shows as a whole, and the
inspection artifact is one more entry the existing components already read.

## Risks / Trade-offs

- [The close commit is not found (history rewritten, shallow clone)] ->
  the trace says it cannot tell and marks nothing (AC-SPECS-018.3).
- [Writing into the archive folder] -> only inspection.md, through the
  read-back writers; every other write to an archived change stays refused.
- [Ranking is subjective] -> each step says why it is where it is, and the
  reviewer can jump or defer.

## Migration / Rollback

None: inspection.md is new and optional; R and V findings route as before.

## Open Questions

None.
