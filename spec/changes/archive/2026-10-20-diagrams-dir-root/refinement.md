# Refinement: diagrams-dir-root

## Problem

`specworks diagrams --dir <folder>` resolves the folder from the working
directory, while every path the CLI prints (`docsPath` in `context`) is relative
to the workspace root. Reproduced in this repo: from `src/specworks/workflow/`,
`diagrams --dir src/specworks/core/docs --check` looks in
`src/specworks/workflow/src/specworks/core/docs`, which doesn't exist, prints
`no diagrams` and exits 0. The close skill runs `specworks diagrams --dir
"<docsPath>"`, so a close run from inside a module silently renders nothing.
Found as suspected bug 13 of `baseline-cli`.

## Context

**Observed:**
- `cli/specs.py`, `diagrams`: `folder = dir.resolve()` (working directory),
  then refuses a folder outside the workspace; a missing folder gives no
  diagrams and exit 0.
- `skills/specworks-close/SKILL.md` step 4: `specworks diagrams --dir
  "<docsPath>"`, with `docsPath` from `specworks context`, root-relative.
- Living spec: `cli` REQ-CLI-008 (diagrams); AC-CLI-008.4 already writes the
  folder root-relative (`--dir src/auth/docs`).

**Assumed:**
- Nobody relies on `--dir` being relative to a subfolder; the skills, the only
  documented caller, pass root-relative paths.

## Constraints

- [hard] The path the CLI prints for a docs folder works as `--dir` from any
  folder of the workspace.
- [hard] A mistyped folder is reported, never a silent success.
- [soft] An absolute path keeps working.

## Options

### Option A: Root-relative, and the folder must exist

A relative `--dir` is resolved from the workspace root; an absolute one is kept.
A folder that doesn't exist fails, naming it.

- **Pros:** The skill works unchanged from anywhere; matches every printed path.
- **Cons:** Differs from a shell path typed inside a subfolder, but the error
  for a missing folder shows where it looked.
- **Effort:** S
- **Touches:** `cli`

### Option B: Working-directory-relative, and the folder must exist

- **Pros:** Behaves like a normal shell path.
- **Cons:** The close skill must build an absolute path; every printed path
  stays unusable from a subfolder.
- **Effort:** S
- **Touches:** `cli`, the close skill

### Option C: Only fail on a missing folder

- **Pros:** Smallest.
- **Cons:** The skill's path still fails from a subfolder, now loudly.
- **Effort:** S
- **Touches:** `cli`

## Recommendation

**Option A**, chosen with the user.

## Open Questions

None.

## Candidate Capabilities

- `cli`: REQ-CLI-008 MODIFIED. `--dir` is relative to the workspace root, and a
  missing folder is refused.
