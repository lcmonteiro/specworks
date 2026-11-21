# Proposal: commit-phase-and-half

## Why

A change's commits do not reliably say which phase made them: in implement both halves commit as
`<ref>: implement`, and `--message` replaces the whole subject, so a project's convention can drop the
phase. `git log` and `/specworks-inspect` (which reads a change's commits by phase) then depend on what
an agent happened to write.

## What Changes

- Every subject `specworks commit` writes starts with `<ref>: <phase>`; in implement it is
  `<ref>: implement (test)` or `<ref>: implement (code)`; an archived change keeps `<ref>: close`.
- `--message` becomes text after that prefix, `<prefix> - <text>`, instead of the whole subject; a
  message that already starts with the prefix is kept as is, not doubled; a message on more than one
  line is refused. **BREAKING** for a caller that used `--message` to write a subject without the phase.
- `specworks commit --half test|code`: required in implement and refused in any other phase (also after
  close). **BREAKING** for a commit in implement without it.
- `specworks merge <branch>` (and the harness's `/merge`, which merges the same way) commits as
  `<ref>: <phase> (merge <branch>)` instead of git's `Merge branch '<branch>'`.
- Skill text: the shared committing text states the subject rule; `/specworks-test` and
  `/specworks-code` commit with `--half test` / `--half code`; `/specworks-inspect` commits with
  `--message "inspect"`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project`: REQ-PROJ-024 (committing a phase) takes its subject from the new REQ-PROJ-036 (a phase
  commit's subject: the prefix, the half, the appended message).
- `cli`: REQ-CLI-012 (`commit`) gains `--half` and `--message` becomes the text after the prefix.
- `workflow`: REQ-FLOW-015 (merging a half's branch) names the merge commit.

## Related requirements

- REQ-PROJ-024 modified
- REQ-CLI-012 modified
- REQ-FLOW-015 modified
- REQ-CLI-010 left: `merge`'s command surface and output do not change; the subject is REQ-FLOW-015's
- REQ-HARNESS-007 left: `/merge` merges "the way `specworks merge` does", so it gets the new subject
  through REQ-FLOW-015 with no wording to change
- REQ-PROJ-013, REQ-PROJ-014 left: matched on "commit" for running commands and reusing results, unrelated

## Impact

- Code: `core/changes.py` (`commit_phase`), `cli/changes.py` (`commit`), `workflow/merge.py`
  (`merge_branch`).
- Skills: `_shared/committing.md`, `specworks-test`, `specworks-code`, `specworks-inspect` (then
  `uv run specworks skills` refreshes `.claude/skills/`); `tests/test_skills.py` checks some wording.
- Assumption: a `--message` that starts with the full prefix (`<ref>: implement (test)`) is kept as
  is, so callers that already wrote a full subject keep working.

## Out of Scope

- Recording the running half on the change, or inferring it from gates or files (rejected in refinement).
- Rewriting past commits' subjects.
- A trailer carrying the phase (rejected in refinement: the subject is what `--oneline` shows).
- Commits made by hand with `git commit` outside specworks.
