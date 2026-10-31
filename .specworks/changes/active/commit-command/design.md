# Design: commit-command

## Context

See proposal.md. `Change` (`src/specworks/core/changes.py`) is saved to
`.change.yaml` by `Change.save`; `set_phase` changes the phase and saves.
`src/specworks/core/git.py` runs git with `git` / `git_text` (UTF-8 paths).
The CLI's `new`, `phase` and `start` move a change's phase; `start` goes
through the gates first. The workspace root can be below the git root.

## Goals / Non-Goals

**Goals:**
- One function that lists the workspace's dirty files with their hashes,
  used both to record and to commit.
- The record is written with the phase, in the same save.

**Non-Goals:**
- Splitting a file's edits from before and during the phase.
- Pushing, merging or amending.

## Decisions

### The record lives in `.change.yaml`, written by `set_phase`

`Change` gets `dirty: dict[str, str]` (path relative to the workspace root
-> SHA-256 hex, or `deleted`), saved under `dirty:` and omitted when empty.
`set_phase(change, phase, root)` records `dirty_files(root)` only when the
phase changes, and `create_change` records it when the change is created.
`dirty_files` reads `git status --porcelain=v1 -z --untracked-files=all`
from the workspace root, keeps the paths under it, and hashes each file's
bytes. Alternative rejected: a hidden git ref (refinement Option B). Serves
REQ-PROJ-023.

### Commit what is not in the record

`commit_phase(ws, change, subject, trailers)` takes `dirty_files(ws.root)`
now, and stages every path under the change folder plus every path that is
missing from `change.dirty` or has another hash; a recorded path that is
still dirty with the same hash is left out. It stages with `git add --` and
the explicit paths (deletions with `git rm --cached --ignore-unmatch --`
where needed), and commits with `git commit -F -` and the message on stdin,
so no shell quoting is involved. Before staging it refuses a detached HEAD.
Serves REQ-PROJ-024.

### Pinned wording

The tests assert these and the code writes them verbatim:

- Subject: `<ref>: <phase>`
- Nothing to commit: `nothing to commit for <ref>: no file changed since the phase started`
- Left out: `left out (unchanged since the phase started): <path>`
- Already dirty: `already dirty when the phase started: <path>`
- Detached HEAD: `cannot commit on a detached HEAD; switch to a branch first`
- Skill text (`_shared/committing.md`): `commit with specworks commit --change "<ref>"`

## Interfaces

Agreed with the user

- `src/specworks/core/git.py` (REQ-PROJ-023, REQ-PROJ-024):
  - `dirty_files(root: Path) -> dict[str, str]` (new): dirty and untracked
    files under `root`, relative to it (POSIX), with the SHA-256 hex of
    their content or `deleted`; raises `GitError` outside a repository.
  - `commit(root: Path, paths: Sequence[str], message: str) -> str` (new):
    stages exactly `paths` (relative to `root`, deletions included), commits
    with `message` on stdin, returns the short hash; raises `GitError`
    (`cannot commit on a detached HEAD; switch to a branch first`) before
    staging anything on a detached HEAD.
- `src/specworks/core/changes.py`:
  - `Change.dirty: dict[str, str]` (extended; default empty, saved under
    `dirty:` only when not empty, read as empty when missing) (REQ-PROJ-023)
  - `set_phase(change: Change, phase: str, root: Path | None = None) -> None`
    (extended, not breaking): with `root`, records `dirty_files(root)` when
    the phase changes, in the same save (REQ-PROJ-023)
  - `create_change(cfg: Config, name: str, root: Path | None = None) -> Change`
    (extended, not breaking): with `root`, records `dirty_files(root)` in
    the first save (REQ-PROJ-023)
  - `CommitResult` (new, frozen dataclass): `commit: str | None` (short hash,
    `None` when nothing was committed), `subject: str`, `committed:
    list[str]`, `left_out: list[str]`, `already_dirty: list[str]`, paths
    relative to the workspace root (REQ-PROJ-024)
  - `commit_phase(root: Path, ref: str, change: Change, subject: str | None = None, trailers: Sequence[str] = ()) -> CommitResult`
    (new): `root` is the workspace root, `ref` the change's ref for the
    default subject `<ref>: <phase>`; nothing to commit returns
    `commit=None` (not an error); a detached HEAD raises `GitError` from
    `commit` before staging (REQ-PROJ-024)
- `src/specworks/workflow/gate.py`: `start_phase` (unchanged signature)
  passes `ctx.ws.root` to `set_phase` (REQ-PROJ-023)
- `src/specworks/cli/changes.py` (REQ-CLI-012): `specworks commit --change
  REF [--message TEXT] [--trailer TEXT]... [--json]` (new); `--json` returns
  `ref`, `commit`, `subject`, `committed`, `leftOut`, `alreadyDirty`; text
  prints `<hash> <subject>`, then one line per committed file and the pinned
  `left out ...` / `already dirty ...` lines, or the pinned nothing-to-commit
  line; an unknown change is the existing `ChangeNotFound` error. `new` and
  `phase` pass `ws.root` to `create_change` / `set_phase` (extended).

Notes on the proposal written at specify: `commit_phase` takes the
workspace root and the ref instead of a `Workspace`, since the default
subject needs the qualified ref (`module:name`) that a `Change` alone does
not know, and `core/changes.py` stays free of `workspace`; `trailers` is a
`Sequence[str] = ()` (ruff B006 rejects a `[]` default).

## Diagrams

No structural change.

## Risks / Trade-offs

- [A large untracked folder makes hashing slow] -> git already lists only
  files outside `.gitignore`; hashing reads each file once per phase move.
- [A file dirty before and during the phase] -> committed whole and flagged
  (AC-PROJ-024.2).
