# Design: add-reopen-change

## Context

Close (`src/specworks/specs/merge.py`) writes the living docs and moves the change to `archive/<date>-<name>/`; `abandon` does the same move without merging. Nothing moves a change back, and the two rules that guard the merge (`check`'s ADDED-already-in-the-living-spec error and the merge's own refusal of it) would reject a reopened change's deltas. See proposal.md for why; the choice of re-merging in place was agreed in refinement.md.

`requirements.md` History already names, for every close, the change and the IDs it added, modified or removed (`HISTORY_LINE_RE`, `history_lines` in `src/specworks/specs/capabilities.py`). Archived names stay taken (REQ-PROJ-010), so only a reopened change can have History lines under its ref.

## Goals / Non-Goals

**Goals:**
- Move a closed change back to `active/` with a mandatory reason and a starting phase, all or nothing.
- Let the second close update the living spec in place for the IDs the change itself merged, and keep every other collision an error.
- Keep the decision about the phase in the skill, and the CLI a plain, checked move.

**Non-Goals:**
- Reopening abandoned changes, unmerging living docs, git operations, telemetry events for reopen.
- Making the skills a capability.

## Decisions

### Reopen lives in the project capability, as a move plus a record

`reopen_change` finds the archived change by name or folder (`archived_as`), refuses it when it is active, abandoned or not found, checks the reason and the phase with the rules `set_phase` uses, records the dirty files (REQ-PROJ-023) before the move, appends a `Reopened` entry to the metadata, then moves the folder with `shutil.move`. When the move raises `OSError`, the metadata is written back as it was (the same pattern as `archive_change`). It does not live in `specs`: it merges nothing. Serves: REQ-PROJ-033, REQ-PROJ-034.

Alternative: put it next to `archive_change` in `merge.py`. Rejected: that module is about merging, and `core` must not import `specs`.

### The record is a list of mappings in `.change.yaml`

`reopened:` holds `{at, reason, phase}` entries, oldest first, written only when there is one, so old metadata reads as never reopened. The reason is free text from the user; it never goes into an event (telemetry is out of scope, and REQ-CLI-017 keeps reasons out of events). Serves: REQ-PROJ-034, REQ-CLI-021.

Alternative: a single `reopened` string like `abandoned`. Rejected: a change can be reopened twice and the first reason is history.

### Own IDs come from History, not from a flag

`own_ids(cap, change_ref)` returns the IDs that History lines naming `change_ref` list as ADDED, MODIFIED or REMOVED. `check` and `plan_merge` call it with the ref close would write (`module.qualify(name)`). Serves: REQ-SPECS-017, REQ-SPECS-006, REQ-SPECS-013.

Alternative: treat every ID of a change with `reopened` entries as own. Rejected: it would also let a reopened change ADD an ID another change put in the living spec in between; History says which change merged which ID, so the narrow rule costs nothing extra.

### The exemptions are narrow

In `check`: an ADDED own ID the living spec has is accepted; a REMOVED own ID it lacks is accepted; a MODIFIED ID it lacks is still an error (another change removed it); an own ADDED ID that is not in the living spec and that History shows removed is still retired (REQ-SPECS-006's own rule). `modified_since` takes an `exclude` ref so the change's own earlier close is not "another change". In the merge: an own ADDED block present in the living spec is replaced in place and returned in `modified` (so the History line says `MODIFIED`), and is not appended again; an own REMOVED ID already gone is skipped and returned nowhere. Serves: REQ-SPECS-017.

### The skill decides the phase; the CLI only records it

`specworks reopen` takes `--phase` (default `review`) and does not interpret the reason. `/specworks-reopen` reads the problem, applies the routing table, says its decision in one line and asks for confirmation. At `review` it adds the problem as a finding with `specworks finding add`, so the review gate and `/specworks-build` act on it; at `refine` and `specify` the phase skills read the reason from `specworks status`. Serves: REQ-CLI-020, REQ-CLI-021.

### Naming an archived change

`reopen` resolves the change with `resolve_archived` (name, module-qualified name, or `<date>-<name>`), like `status`. When no archive holds that name, it asks `resolve_change` and, if the change is active, says so instead of "not found". Serves: REQ-CLI-002, REQ-CLI-020.

### Pinned wording

The skill tests are untagged (the skills have no capability yet). The test half asserts these phrases and the code half writes them verbatim:

- `/specworks-reopen`'s `description` frontmatter: `Use` followed by text holding `specworks` and `"specworks reopen"`.
- The command line: `specworks reopen --change "<ref>" --reason "<reason>" --phase <phase>`.
- The confirmation: `Reopen <ref> at <phase>? (yes/no)`.
- The reason rule: `The reason comes from the user; never invent it.`
- The earliest-phase rule: `the earliest phase any of them needs`.
- The finding for a `review` start: `specworks finding add`.
- The commit: `--message "<ref>: reopen"`.
- The boundary: `does not switch branches, rebase or push`.
- `/specworks-refine` and `/specworks-specify`, in the step that loads what exists: "When the change was reopened, the latest reason in specworks status is the problem to start from."

## Interfaces

Agreed with the user

- `src/specworks/core/changes.py`: `@dataclass(frozen=True) class Reopened` with `at: str`, `reason: str`, `phase: str` (REQ-PROJ-034).
- `src/specworks/core/changes.py`: `Change.reopened: list[Reopened]`, saved and read as the `reopened` list of `{at, reason, phase}` (REQ-PROJ-034).
- `src/specworks/core/changes.py`: `reopen_change(cfg: Config, name: str, reason: str, phase: str = "review", root: Path | None = None) -> Change`, raising `ChangeError` (and `ChangeNotFound` for a name no archive or `active/` has) (REQ-PROJ-033, REQ-PROJ-034).
- `src/specworks/specs/capabilities.py`: `own_ids(cap: CapabilityRef, change_ref: str) -> set[str]` (REQ-SPECS-017).
- `src/specworks/specs/capabilities.py`: `modified_since(cap: CapabilityRef, since: str, exclude: str = "") -> dict[str, str]`, skipping the History lines of the change `exclude` (REQ-SPECS-017).
- `src/specworks/specs/merge.py`: `apply_delta(living_text: str, delta: Delta, own: frozenset[str] = frozenset()) -> tuple[str, list[str], list[str], list[str]]` (REQ-SPECS-017, REQ-SPECS-013).
- `src/specworks/cli/changes.py`: `specworks reopen --change <ref> --reason "<why>" [--phase <phase>] [--json]` (REQ-CLI-020).
- `src/specworks/cli/output.py`: `change_dict` carries `reopened` (a list of `{at, reason, phase}`) when the change has entries; `status` text appends the count and the latest reason (REQ-CLI-021).
- The new skill `/specworks-reopen` (its SKILL.md in the skills folder), written in the code half (task 4.2): a skill file is text with no stub form, and an unfinished one would fail the per-skill tests.

## Diagrams

No structural change: the new code sits in existing modules and the dependencies between them stay the same (`cli` and `specs` call `core`; `core` does not import `specs`).

## Risks / Trade-offs

- [Hand-edited History could make an ID look like the change's own] -> History is generated by close and the repo says never to edit it; the exemption only removes an error, it cannot add a requirement.
- [Another change closed in between and edited a block the reopened change MODIFIES] -> the existing "MODIFIED after this change started" warning still fires for that change's lines; only the change's own lines are skipped.
- [The skill routes a problem to the wrong phase] -> it states its decision and waits for the user's yes; the user can name another phase.
- [A reopened change loses its place in the dirty record] -> the record is retaken before the move, as for any phase move, so the commit holds the files of the move and nothing the user had before.

## Migration / Rollback

None: `reopened` is optional, and metadata without it reads as never reopened. Rollback is `git revert` of the reopen commit.

## Open Questions

None.
