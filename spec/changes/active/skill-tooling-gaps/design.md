# Design: skill-tooling-gaps

## Context

Only packaged skill text (`src/specworks/skills/`), its installed copies,
`.gitignore` and the wording checks in `tests/test_skills.py` change; see
proposal.md for the four gaps. The change is `skip-specs`: no requirement IDs.

## Interfaces

None: the change edits skill text and repo tooling only; no Python API, CLI
command, data shape or error is added or changed.
