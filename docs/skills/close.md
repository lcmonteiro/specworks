# /specworks-close

:Phase: close (last; the change ends `done`)
:Writes: the living docs in `<capability path>/<docs_dir>/`; the config for new capabilities
:Next: commit code, living docs and archive together
:Example: {doc}`../tutorial/close`

Turn what the change decided into the project's lasting truth: the deltas are
merged into each capability's living spec next to its code, the design
knowledge worth keeping moves there too, and the change folder is archived.
Use it when a change has passed validate, or when you say "close the change",
"archive the change" or "merge the specs".

## Steps

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 1 | Start the phase | `specworks start close --change <ref>` | `gate validate`; failures point to `-> /specworks-<phase>` |
| 2 | Register new capabilities | `specworks spec show <ref> --json` (`"new": true`), then `specworks capability add <name> --path ... [--prefix <P>]` | the prefix the delta's IDs already use (confirmed with you) |
| 3 | Show the merge plan | `specworks close --change <ref> --dry-run --no-run` | per capability: living spec (new or existing), requirements ADDED / MODIFIED / REMOVED. Asks "Merge and archive?" |
| 4 | Living design and architecture | `specworks context --json` (`docsPath`); `specworks diagrams --dir <docsPath>` | where to write `design.md`, `architecture.md`, `diagrams/` |
| 5 | Merge and archive | `specworks close --change <ref>` | `merged ... -> ...`, `archived -> ...` |
| 6 | Report and stop | — | docs written, requirements changed, capabilities registered, archive path |

## What `specworks close` does

1. Runs validate with fresh project commands; refuses a change that does not
   pass, and a living spec that `check` finds broken.
2. Applies every delta to `spec.md`: ADDED appended, MODIFIED replaced in
   place by ID, REMOVED deleted, everything else kept.
3. Regenerates `requirements.md`: the index of requirements and criteria, and
   a History line for this change.
4. Sets the phase to `done` and moves the change to
   `<dir>/changes/archive/<date>-<name>/`.

## Living design.md

The lasting design of the capability as it is now, not the story of the
change: Overview, Decisions (each with why, alternatives, and the change that
introduced it), Interfaces, Constraints. Decisions review.md overturned are
dropped; task-level detail is left out. `architecture.md` only when the change
altered structure.

## Guardrails

- Never closes a change that does not pass validate.
- Never edits `spec.md` or `requirements.md` by hand: `specworks close` writes
  them. Requirements change through a new change.
- Living docs describe the system now; history belongs in the archive and in
  `requirements.md`'s History.
- Asks before registering a capability and before merging.

## Source

````{dropdown} specworks-close/SKILL.md
:icon: code

```{literalinclude} ../../src/specworks/skills/specworks-close/SKILL.md
:language: markdown
```
````
