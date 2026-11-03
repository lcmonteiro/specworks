# Design: project-docs

## Context

See proposal.md. A module's root and its `docs_dir` are already known
(`Module.root`, `Module.config.docs_dir` in `src/specworks/core/workspace.py`);
`context` builds module entries with `module_dict` (`src/specworks/cli/output.py`);
`close` (`src/specworks/cli/workflow.py`) runs validate, plans the merge and
archives; validate's `diagrams_current` (`src/specworks/workflow/validate.py`)
checks the change folder's diagrams with `diagrams_in` and `state`
(`src/specworks/tools/diagrams.py`). Shared skill text lives in
`src/specworks/skills/_shared/<name>.md` and is pulled in with
`<!-- specworks:include <name> -->`.

## Goals / Non-Goals

**Goals:**
- The CLI knows where a module's architecture is and says whether it exists;
  close cannot finish without it.
- The structure and the update rules live once, in shared skill text.

**Non-Goals:**
- No check of the architecture's content or size by the CLI.

## Decisions

### The docs folder belongs to the module

`Module.docs_path` is `root / config.docs_dir` and `Module.architecture_path`
is `docs_path / "architecture.md"`. No new config key: `docs_dir` already names
the docs folder of every capability. A capability on `.` gets the same folder;
its files (`spec.md`, `requirements.md`, `design.md`, `diagrams/<cap>-blocks.d2`)
and the architecture's (`architecture.md`, `diagrams/architecture-blocks.d2`)
do not overlap. Serves: REQ-PROJ-029.

### Close refuses before validate

The check runs first, so a missing file fails fast without running the
project's commands; `--dry-run` runs validate as today and reports the file
under `missing` (JSON) and a `missing: <path> (write it before close)` line, so
the close skill learns it from its dry run. Serves: REQ-CLI-007.

### Validate warns on the module's architecture diagrams

A new coherence check, `architecture_diagrams_current`, runs `state` on every
diagram in `<module docs>/diagrams/` and warns (non-blocking, fix
`/specworks-close`) naming each stale or missing SVG; it returns `None` when
the folder has no diagram. A capability on `.` shares that folder, so its own
block diagram is checked here too, which is harmless. Serves: REQ-FLOW-013.

### Skills: two shared texts

- `_shared/architecture.md`: the structure and rules, included by close
  (its living-docs step), adopt and start.
- `_shared/reading-architecture.md`: the reading line, included by refine,
  specify, design, review and onboard.

Close checks the architecture after the capabilities' `design.md` and before
`specworks close`, so the close command finds it. Serves: REQ-PROJ-029.

**Pinned wording** (the test half asserts each line of these blocks; the code half writes them, verbatim):

In `_shared/architecture.md`:

```text
`<docsPath>/architecture.md`
`<docsPath>/diagrams/architecture-blocks.d2`
## Overview
## Capabilities and how they interact
## Architectural decisions
## Glossary
Keep it to about 150 lines: merge or drop entries rather than grow it.
Update it when the change adds or removes a capability, changes what flows between capabilities, adds a decision that spans capabilities, or adds a term; otherwise leave it as it is.
When it is missing, write it now, before `specworks close`.
```

In `_shared/reading-architecture.md`:

```text
Read the module's `<docsPath>/architecture.md` first (`docsPath` of the module in `specworks context`); when there is none yet, go on without it.
```

Each of close, adopt and start contains `<!-- specworks:include architecture -->`;
each of refine, specify, design, review and onboard contains
`<!-- specworks:include reading-architecture -->`.

## Interfaces

Agreed with the user

- `src/specworks/core/workspace.py`: `ARCHITECTURE_FILE = "architecture.md"`; `Module.docs_path -> Path` and `Module.architecture_path -> Path` (properties) (REQ-PROJ-029)
- `src/specworks/cli/output.py`: `module_dict` entries gain `docsPath` (relative to the workspace root) and `hasArchitecture` (REQ-CLI-004)
- `src/specworks/cli/workflow.py`: `close` refuses `<ref> has no <path>: write the module's architecture before close (/specworks-close)` before validate; with `--dry-run`, JSON `missing: [<path>]` (empty when present) and the text line `missing: <path> (write it before close)` (REQ-CLI-007)
- `src/specworks/workflow/validate.py`: `architecture_diagrams_current(ctx: GateContext) -> Check | None`, listed in `VALIDATE` under coherence, fix `/specworks-close` (REQ-FLOW-013)
- `src/specworks/skills/_shared/architecture.md` and `src/specworks/skills/_shared/reading-architecture.md` (new), included as pinned above

Stubs (tasks 1.1, 3.1): `ARCHITECTURE_FILE` in full; `Module.docs_path` and
`Module.architecture_path` return `root` and `root / ARCHITECTURE_FILE` until
the code half (nothing calls them yet); `architecture_diagrams_current` returns
`None` (no check), so validate's existing checks keep passing. `module_dict`'s
new keys and close's refusal have no stub: they are behaviour, written by the
code half. The two shared skill texts exist as one-line placeholder comments
(no skill includes them yet); the code half writes their pinned wording (4.2).

## Diagrams

No structural change: new properties and one check inside existing components.

## Risks / Trade-offs

- [Sample projects in the tests that run `close` have no architecture] -> the
  test half's helpers write a `docs/architecture.md` for them.
- [The file grows on every close] -> the pinned 150-line rule, read at every close.
- [This repo's next close fails on the missing file] -> this change's own close
  writes the first `docs/architecture.md`.

## Migration / Rollback

Existing projects: the first close after upgrading writes the file (the close
skill does it before `specworks close`).

## Open Questions

None.
