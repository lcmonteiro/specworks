# Review: docs-active-path

Base: `origin/main`

## Findings

None.

Checked against proposal.md and design.md (the change is `skip-specs`, so there
are no requirements or criteria): `CLAUDE.md` says `spec/changes/active/` holds
the work in flight, and the `init` line of `README.md` lists
`spec/changes/active/` and `spec/changes/archive/`. design.md has no
interfaces to compare.

## Changed files without tags

The branch is stacked on `active-changes-dir`, whose pull request is not merged
yet, so the diff against `origin/main` also holds that change's test edits:

- `tests/helpers.py`: path-only update (`spec/changes/active/<ref>`) made by `active-changes-dir`; this change does not touch it
- `tests/test_walkthrough.py`: path-only update of the `C` constant made by `active-changes-dir`; this change does not touch it

This change's own files, `CLAUDE.md` and `README.md`, carry no tags in a
`skip-specs` change.

## Summary

No drift found; nothing was sent back to an earlier phase.
