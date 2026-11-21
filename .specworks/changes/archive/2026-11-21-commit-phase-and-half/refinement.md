# Refinement: commit-phase-and-half

## Problem

A specworks change's commits do not reliably say which phase made them, nor which half of implement.
The default subject `<ref>: <phase>` reads `<ref>: implement` for both the test half and the code half,
and `--message` replaces the whole subject, so a project's commit convention can drop the phase
altogether. The `git log` of a change is then only as readable as the agent that happened to write it,
and `/specworks-inspect`, which reads a change's commits by phase, cannot rely on it.

## Outcomes

- Every commit `specworks commit` makes has a subject that starts `<ref>: <phase>`, and in implement
  `<ref>: implement (test)` or `<ref>: implement (code)`; `git log --oneline` shows it.
- A project's own text given with `--message` follows that prefix instead of replacing it.
- A commit in implement that does not say its half is refused, with an error that says how to give it.
- The commit merging the test half's worktree branch (`specworks merge`) reads
  `<ref>: implement (merge test)` instead of git's `Merge branch '…'`.

## Context

**Observed:**
- `core/changes.py` `commit_phase` builds the default subject `f"{ref}: {'close' if archived else change.phase}"`
  and uses `--message` as the whole subject when given (REQ-PROJ-024, `project`).
- `cli/changes.py` `commit` exposes `--message` and `--trailer` (REQ-CLI-012, `cli`).
- `HALVES = ("test", "code")` in `core/changes.py`: halves are gate names and task markers, not phases;
  the change records no current half (`gate test` / `gate code` check only their half).
- `workflow/merge.py` merges a branch with `git merge --no-ff --no-edit` and, after resolving conflicts,
  `git commit --no-edit`: git's default message (`workflow`).
- `_shared/committing.md` tells every skill the subject is `<ref>: <phase>` and to pass `--message` for a
  project convention; `specworks-test` and `specworks-code` include it.
- `specworks-inspect` commits with `--message "<ref>: inspect"` and lists a change's commits with
  `git log --grep "<ref>:"`.
- This repo's history has subjects such as `<ref>: new change`, `<ref>: start close`,
  `<ref>: implement (cycle 2: R1 test, R2 welcome)`: the phase there was the agent's choice.

**Assumed:**
- No tool outside specworks parses these subjects, so changing the default text breaks nobody.

## Constraints

- [hard] The half is never guessed: it is given explicitly, or the commit is refused.
- [hard] `--message` and `--trailer` keep working; trailers are unchanged.
- [hard] Skills are edited in `src/specworks/skills/` and refreshed with `uv run specworks skills`;
  `tests/test_skills.py` checks some wording verbatim.
- [soft] The subject stays one short line, readable in `git log --oneline`.

## Options

### Option A: `specworks commit --half test|code`

`commit` takes `--half`; in implement it is required and becomes `(test)` / `(code)` in the subject,
in any other phase it is refused. `--message` text is appended after the prefix. The test and code
skills pass their half; `specworks merge` writes `<ref>: implement (merge test)`.

- **Pros:** explicit, nothing is inferred; one flag, one line per half skill.
- **Cons:** a new required flag in implement: an old call without it now fails.
- **Effort:** S
- **Touches:** `project`, `cli`, `workflow` (merge), the committing skill text
- **Outcomes:** meets all four.

### Option B: the last gate run in the checkout

`gate test` / `gate code` records the half on the change; `commit` reads it.

- **Pros:** no new flag.
- **Cons:** implicit state; a commit before the gate has no half, and a build without worktrees runs
  both halves in one checkout and can label a commit with the wrong one.
- **Effort:** M
- **Touches:** `project`, `workflow`, `cli`
- **Outcomes:** meets the prefix outcomes only partly; can mislabel the half.

### Option C: infer the half from the files committed

Only tests → `test`, only source → `code`.

- **Pros:** no flag, no state.
- **Cons:** a test half also ticks `tasks.md`, a code half may touch tests: the guess is unreliable.
- **Effort:** S
- **Touches:** `project`, `cli`
- **Outcomes:** fails "the half is never guessed".

## Recommendation

Option A (agreed): `--half test|code`, required in implement and refused elsewhere; `--message` appended
after the `<ref>: <phase>[ (<half>)]` prefix; the merge commit named `<ref>: implement (merge test)`.

## Open Questions

- The separator between the prefix and `--message` text (e.g. `<ref>: implement (test): <text>` or
  `<ref>: implement (test) - <text>`), and whether a `--message` already starting with the prefix is
  kept as is rather than doubled. (who can answer: the user, at specify)
- `specworks-inspect` commits `<ref>: inspect`, and inspect is not a phase: should its commit read
  `<ref>: <phase>: inspect` like any other message, or keep a subject of its own? (who can answer: the user, at specify)

## Candidate Capabilities

- `project`: modified - the commit subject always carries the phase and, in implement, the half;
  `--message` follows the prefix (REQ-PROJ-024).
- `cli`: modified - `commit --half test|code`, required in implement and refused elsewhere (REQ-CLI-012).
- `workflow`: modified - the merge of a half's branch commits as `<ref>: implement (merge test)`.
