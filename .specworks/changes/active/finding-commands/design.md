# Design: finding-commands

## Context

See proposal.md. `src/specworks/workflow/review.py` reads review.md
(`parse_review`, `read_review`, `Finding`, `ReviewDoc`) with the regexes and
tables the writers must agree with (`FINDING_RE`, `TYPE_PHASE`, `BACK_RE`,
`DONE_RE`, `FINDING_STEPS`). The CLI groups (`task`, `spec`, `module`,
`capability`) are `App` instances in `src/specworks/cli/app.py`, with their
commands in the module of their area. `save_tools`
(`core/config_file.py`) is the model for an edit that is checked by reading
the file back.

## Goals / Non-Goals

**Goals:**
- One writer per kind of line, each validated with the reader's own rules.
- A write is all or nothing: the file changes only when it reads back as
  expected.

**Non-Goals:**
- Changing what `parse_review` accepts.
- Rewriting or reformatting any existing line.

## Decisions

### Edit the text, then read it back

Each writer reads review.md, finds the finding's block (its checkbox line
and the indented lines after it, as `parse_review` sees them), builds the
new text by inserting one line at the end of the block (or replacing the
Decision line, or ticking the box), parses the new text, and checks that the
finding reads back as expected (ID, state, step). Only then is the file
written; otherwise a `FindingError` names the problem and nothing is
written. Alternative rejected: a structured data file with review.md
generated from it (refinement Option B). Serves REQ-FLOW-016.

### A new review.md has the template's headings, not its example lines

When review.md does not exist, `add_finding` writes the template's title,
`Base:` line, headings and guidance comments, without its example finding
and example file lines, which would read as an unreadable finding. Serves
REQ-FLOW-016 (AC-FLOW-016.2).

### The confirmation line

`close_finding` ticks the box and adds `  - confirmed in review: <text>`.
`parse_review` does not route on it (only the box counts), so nothing it
reads changes.

### Pinned wording

The tests assert these and the code writes them verbatim:

- Proposal line: `  - **Proposal**: <proposal>`
- Decision line: `  - **Decision**: <decision>`
- Done line: `  - done in <step>: <text>`
- Confirmation line: `  - confirmed in review: <text>`
- Unknown finding: `no finding <id> in <review.md path>`
- Decision in another form: `a decision starts with 'back to <step>:' (specify, design, implement, test or code) or 'accepted:'`

## Interfaces

Proposed: waiting for the user's agreement

- `src/specworks/workflow/review.py` (REQ-FLOW-016):
  - `class FindingError(SpecworksError)`: every refusal (unknown finding,
    type or step, empty text, a decision in another form, a block that does
    not read back); its message names the problem, using the pinned wording
    above.
  - `add_finding(change: Change, kind: str, text: str, proposal: str) -> Finding`:
    `kind` is one of `TYPE_PHASE` (`kind`, not `type`, so the builtin is not
    shadowed; `Finding.type` is unchanged).
  - `decide_finding(change: Change, finding_id: str, decision: str) -> Finding`
  - `mark_finding_done(change: Change, finding_id: str, step: str, text: str) -> Finding`:
    `step` is one of specify, design, implement, test, code (what `DONE_RE` reads).
  - `close_finding(change: Change, finding_id: str, text: str) -> Finding`
  - each returns the finding as `read_review` reads it after the write, and
    raises `FindingError` with review.md left as it was.
- `src/specworks/cli/app.py`: `finding_app = App(help="Write a change's review findings (review.md).")`, added as `specworks finding` (REQ-CLI-011).
- `src/specworks/cli/workflow.py` (REQ-CLI-011): the commands, as
  `finding_add`, `finding_decide`, `finding_done` and `finding_close`
  registered on `finding_app`:
  - `finding add TYPE TEXT --proposal TEXT --change REF [--json]`
  - `finding decide ID DECISION --change REF [--json]`
  - `finding done ID TEXT --in STEP --change REF [--json]`
  - `finding close ID TEXT --change REF [--json]`
  - `--json` output: the change (`change_dict`), plus
    `"finding": {**Finding.to_dict(), "done": <bool>}` (`id`, `type`,
    `text`, `phase`, `doneIn` when set, and its state) and `"path"`,
    review.md relative to the workspace root. `done` is added here, not to
    `Finding.to_dict()`, so `specworks cycle`'s output is unchanged.
  - text output: one line, `<id> <type> -> <phase> (open|done)` then the path.
  - errors: `FindingError` reaches the `App` wrapper (`{"error": ...}`, exit 1).

## Diagrams

No structural change.

## Risks / Trade-offs

- [A hand-written block the reader accepts but the writer places a line in
  oddly] -> the read-back check refuses and leaves the file as it was;
  AC-FLOW-016.6 covers a `*` bullet with a bold ID and comments.
