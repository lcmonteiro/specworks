# Design: commit-phase-and-half

## Context

`commit_phase` (`src/specworks/core/changes.py`) builds the subject inline: the given `subject`, or
`<ref>: <phase>` (`close` once archived). `specworks commit` (`src/specworks/cli/changes.py`) passes
`--message` straight through as that subject. `merge_branch` (`src/specworks/workflow/merge.py`)
commits with `git merge --no-ff --no-edit`, and after resolving conflicts `git commit --no-edit`:
git's own `Merge branch '<branch>'`. The change records no running half (`HALVES` names gates and task
markers only). See proposal.md for why.

## Goals / Non-Goals

**Goals:**
- One function owns the subject rule, so `commit` and its refusals agree (REQ-PROJ-036).
- The refusals happen before anything is staged.
- The merge commit carries the change's ref and phase on both of its paths (clean and resolved).

**Non-Goals:**
- Recording or inferring the half; a phase trailer; rewriting old commits.

## Decisions

### A pure `phase_subject` beside `commit_phase`

`phase_subject(ref, change, half, message)` returns the subject or raises `ChangeError`;
`commit_phase` calls it first, before `dirty_files` or staging, so every refusal leaves the index
untouched (AC-PROJ-036.6–.9). Alternative: validate in the CLI. Rejected: the rule is the project's
(REQ-PROJ-036), and a CLI check would let another caller (the harness) commit without a half.
Serves: REQ-PROJ-036, REQ-PROJ-024.

### The rule, in order

1. `phase = "close"` when the change is archived (`done`), else `change.phase`.
2. Half: in `implement`, `half` must be `test` or `code` (`HALVES`), else refused — none:
   "say which half: --half test or --half code"; another value: "unknown half '<h>': expected test or
   code". Outside implement any half is refused: "a half (--half) is only for implement; <ref> is in
   <phase>". The unknown-half check comes first, so `--half docs` in review names `test` and `code`.
3. `prefix = f"{ref}: {phase}"`, plus `f" ({half})"` in implement.
4. Message: `None` or blank → the prefix; a message containing `\n` or `\r` → refused ("the message
   is one line; put trailers in --trailer"); a message that starts with the prefix → kept as is
   (stripped); otherwise `f"{prefix} - {message.strip()}"`.

Serves: REQ-PROJ-036.

### `commit_phase`'s `subject` parameter becomes `message`

It is no longer the subject, and keeping the old name would invite passing a whole subject. The only
callers are the CLI and `tests/project/test_commit.py`. Serves: REQ-PROJ-024.

### The merge names itself with `-m`

The clean path becomes `git merge --no-ff -m <subject> <branch>`; the resolved path
`git commit -m <subject>` instead of `--no-edit`. The subject is
`f"{module.qualify(change.name)}: {change.phase} (merge {branch})"`, computed before merging. No half
is involved, so `merge` needs no new option. The harness's `/merge` calls the same `merge_branch` and
gets the same subject. Serves: REQ-FLOW-015.

### Skill text

The shared `committing.md` keeps its include (every skill uses it, so it gains no parameter); the
test and code skills add one line after the include. Pinned wording (verbatim, checked by
`tests/test_skills.py` against the filled skill text):

- `_shared/committing.md`: ``the subject is `<ref>: <phase>`, and `<ref>: implement (<half>)` in implement``
  and ``a message given with `--message "<text>"` follows it: `<ref>: <phase> - <text>` ``
- `specworks-test/SKILL.md`: `specworks commit --change "<ref>" --half test`
- `specworks-code/SKILL.md`: `specworks commit --change "<ref>" --half code`
- `specworks-build/SKILL.md` (the worktree's commit): `--half test`
- `specworks-inspect/SKILL.md`: `specworks commit --change "<ref>" --message "inspect"`

## Interfaces

Proposed: waiting for the user's agreement

- `src/specworks/core/changes.py`: `phase_subject(ref: str, change: Change, half: str | None = None, message: str | None = None) -> str`;
  raises `ChangeError` (REQ-PROJ-036).
- `src/specworks/core/changes.py`: `commit_phase(root: Path, ref: str, change: Change, message: str | None = None, trailers: Sequence[str] = (), half: str | None = None) -> CommitResult`
  (was `subject=`; REQ-PROJ-024).
- `src/specworks/cli/changes.py`: `specworks commit --change <ref> [--half test|code] [--message <text>] [--trailer …] [--json]`;
  `--json` keeps `subject` (REQ-CLI-012); `--half` is a plain `str` option (not a typer choice), so `phase_subject`
  validates it and an unknown half is the CLI's `{"error": …}` with exit 1, like every other refusal; `--message`'s
  help becomes "text after the subject's prefix" (REQ-CLI-012).
- `src/specworks/workflow/merge.py`: `merge_branch(ws, module, change, branch)` unchanged in signature;
  its merge commit's subject is `<ref>: <phase> (merge <branch>)` (REQ-FLOW-015).

## Diagrams

No structural change.

## Risks / Trade-offs

- [A caller in implement without `--half` now fails] -> the error names both flags; the skills that
  commit in implement pass it.
- [A `--message` used as a full custom subject now gets the prefix] -> a message already starting with
  the prefix is kept, so an agent that writes the full subject is unaffected.
- [A worktree branch name in the merge subject is noisy (`worktree-agent-ab12`)] -> it is a fact
  `git log` can check; guessing the half was rejected.

## Open Questions

None.
