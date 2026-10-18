# Who writes which file

| File | Written by |
|---|---|
| `<dir>.yml` | `specworks init`, `capability add`, `module add`; you or `/specworks-adopt` (`context`, `commands`) |
| `.change.yaml` | `new`, `phase`, `start` (phase, `specified`), `skip-specs`, `abandon`, `close` |
| `refinement.md` | `/specworks-refine` |
| `proposal.md`, `specs/**/spec.md`, `tasks.md` | `/specworks-specify` (review may make small, agreed edits) |
| `design.md` | `/specworks-specify` (Decisions), `/specworks-design` (Interfaces), `/specworks-review` (agreed edits) |
| task checkboxes | `specworks task done` / `undo` |
| `diagrams/*.svg` | `specworks diagrams` |
| `traceability.md` | `specworks trace --write` |
| `review.md` | `/specworks-review`, plus `done in <phase>:` lines from later phases |
| tests (`@ac`) | `/specworks-test` |
| stubs; code (`@req`) | `/specworks-design`; `/specworks-code` |
| living `spec.md`, `requirements.md` | `specworks close` only, never by hand |
| living `design.md`, `architecture.md`, `diagrams/` | `/specworks-close` |
| `changes/archive/<date>-<name>/` | `specworks close`, `specworks abandon` |
| `.claude/skills/`, `.github/skills/`, `.github/prompts/` | `specworks init`, `specworks skills` |
| `.git/specworks-runs.json` | every command that runs a project command ([The run cache](Reference-Run-Cache)) |

The CLI never writes your code, your tests or your specs; the skills do, each
in its own phase.
