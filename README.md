# specworks

[![CI](https://github.com/lcmonteiro/specworks/actions/workflows/ci.yml/badge.svg)](https://github.com/lcmonteiro/specworks/actions/workflows/ci.yml)

Spec-driven development for AI coding agents, inspired by
[OpenSpec](https://github.com/Fission-AI/OpenSpec) and written in Python (managed with `uv`).

```
refine -> propose -> test -> implement -> review -> verify -> close
```

| Phase     | Skill                  | Output |
|-----------|------------------------|--------|
| refine    | `/specworks-refine`    | `refinement.md`: problem, context, constraints, options, recommendation |
| propose   | `/specworks-propose`   | `proposal.md`, delta specs (requirements + acceptance criteria), `design.md`, `tasks.md`, `traceability.md` |
| test      | `/specworks-test`      | API stubs from the design's interfaces + failing tests tagged `@ac` for every acceptance criterion |
| implement | `/specworks-implement` | implementation driven by tasks and specs *(planned)* |
| review    | `/specworks-review`    | fixes code <-> spec drift; **may edit** code and spec deltas *(planned)* |
| verify    | `/specworks-verify`    | pass/fail report (completeness, correctness, traceability); **read-only** gate before close *(planned)* |
| close     | `/specworks-close`     | living docs merged into `<capability-path>/docs/`, change archived (phase `done`) *(planned)* |

The flow is not strictly linear: `review` can send a change back to `propose`
(missing requirement) and a failing `verify` sends it back to `implement`.
`specworks phase <change> <phase>` moves a change to any phase.

## Layout

```
<dir>.yml                          # config: context, capabilities -> code paths, modules
<dir>/changes/<name>/              # in-flight change artifacts
<dir>/changes/archive/             # finished changes
<capability-path>/<docs_dir>/      # living docs, next to the code
```

The config file is named after the workflow folder: `specworks init --dir spec`
creates `spec.yml` and `spec/` (or `docs.yml` + `docs/`, `context.yml` + `context/`, ...).
`<dir>` defaults to `specworks`. To rename later, rename both the file and the folder.
The file starts with `specworks: 1`, which marks it as a specworks config (so an
unrelated `docs.yml` is never mistaken for one).
`<docs_dir>` defaults to `docs`.

## Specs, IDs and traceability

A change describes behaviour changes as **delta specs**, one per capability, at
`<dir>/changes/<change>/specs/[<module>/]<capability>/spec.md`:

```markdown
## ADDED Requirements

### Requirement: REQ-AUTH-003 Password reset
The system SHALL email a single-use reset link valid for 30 minutes.

#### Scenario: AC-AUTH-003.1 Request reset
- **WHEN** a user asks for a reset with a known email
- **THEN** a reset link is emailed
```

- Requirements are `REQ-<prefix>-NNN`; their acceptance criteria are
  `AC-<prefix>-NNN.<n>`. The prefix is the capability name in upper case
  (`billing:invoices` -> `BILLING-INVOICES`) or the capability's `prefix:` in the config.
- `## MODIFIED Requirements` repeats a whole existing block (same ID);
  `## REMOVED Requirements` needs **Reason** and **Migration**. IDs are never reused.
- `close` merges the deltas into the living spec next to the code
  (`<capability path>/<docs_dir>/spec.md`).
- Tests and code point back with comment tags in any language:
  `# @ac AC-AUTH-003.1` in a test, `// @req REQ-AUTH-003` in code.

| Command | What it does |
|---|---|
| `specworks spec list` / `spec show <ref>` | capabilities, their requirements, ID prefix, next free ID and delta path |
| `specworks validate --change <ref>` | checks proposal, delta specs (IDs, SHALL/MUST, scenarios, MODIFIED/REMOVED targets, ID clashes with other changes) and tasks (format, every AC covered) |
| `specworks diagrams --change <ref> [--check]` | renders the change's `diagrams/*.d2` to SVG with the workspace theme; `--check` reports missing/outdated SVGs without rendering |
| `specworks task list\|done\|undo --change <ref> [N.M ...]` | lists tasks with their IDs; ticks or unticks checkboxes without touching the rest of `tasks.md` |
| `specworks gate <phase> --change <ref>` | checks a phase is finished: `propose` (valid specs, tasks cover every AC), `test` (every AC has an `@ac`-tagged test, no tags to unknown IDs) |
| `specworks trace --change <ref> [--write]` | REQ -> AC -> tasks -> tests (`@ac`) -> code (`@req`) matrix and its gaps; `--write` saves `traceability.md` |

## Diagrams

Designs use [D2](https://d2lang.com) for diagrams: the agent writes a short
text file (`diagrams/<name>.d2`) and `specworks diagrams` renders it to SVG,
which `design.md` embeds. The source stays reviewable in diffs, the SVG looks
good on GitHub, and every diagram shares one theme set in the top-level config:

```yaml
diagrams:
  theme: neutral-default   # by name or number: c4, colorblind-clear, cool-classics, origami, ...
  dark_theme: dark-mauve   # used in dark mode; dark-flagship-terrastruct, or none
  layout: elk              # or dagre
  sketch: false            # true for a hand-drawn look
```

`specworks diagrams --themes` lists every theme and the one in use, and
`specworks init --diagram-theme c4` sets it when creating the project. Changing
the theme marks every SVG as outdated until `specworks diagrams` re-renders it.

Each SVG is stamped with a hash of its source and these settings, so
`specworks validate` (and `diagrams --check`, e.g. in CI) can tell when one is
outdated.

D2 comes with specworks: installing it also installs the official, pinned D2
release for your platform (see [Install](#install)), so every machine renders
identical SVGs. `specworks diagrams --themes` shows which `d2` is used.

## Modules (sub-projects)

Like git submodules, a project can link other folders that have their own
config. Each module is a complete project (own context, capabilities and
changes), and the parent lists it explicitly:

```yaml
# spec.yml (top level)
specworks: 1
modules:
  billing: services/billing
```

```
repo/
  spec.yml                # top level: lists billing
  spec/changes/           # cross-module changes
  services/billing/
    spec.yml              # module: lists tax
    spec/changes/         # billing's own changes
    src/invoices/docs/    # living docs of billing:invoices
    tax/spec.yml          # nested module billing/tax
```

- `specworks module add <path>` (or `specworks init <path>` under a project) creates and links a module.
- Every module uses the **same config and folder name** as the top level (set once by
  `specworks init --dir ...`): `spec.yml` + `spec/` everywhere. A module with another
  name (e.g. `docs.yml`) is an error that says what to rename.
- Commands act on the **nearest** module; `--all` shows the whole workspace.
- Context is **inherited**: top-level context first, then each module down to the current one.
- Capabilities and changes of other modules are named `module:name` (`billing:invoices`, `billing/tax:add-vat`).
- A listed module whose folder has no config (e.g. a submodule not checked out) shows up under `missingModules`.

## Install

```bash
uv tool install git+https://github.com/lcmonteiro/specworks
cd your-project && specworks init --dir spec   # writes spec.yml, spec/ and the agent skills
```

The install includes [D2](https://d2lang.com) for diagrams. When uv builds
specworks, a build hook (`hatch_build.py`) downloads the official D2 release
pinned in `src/specworks/d2_release.json` for your platform (Linux, macOS and
Windows on x86-64 and ARM64), checks its SHA-256, and ships it inside the
package. Downloaded archives are cached, so reinstalling does not download
again.

| Variable | Effect |
|---|---|
| `SPECWORKS_D2` | use this `d2` instead of the bundled one |
| `SPECWORKS_D2_BUNDLE=0` | build without D2 (e.g. offline); `d2` is then looked up on `PATH` |
| `SPECWORKS_D2_PLATFORM` | build the wheel for another platform, e.g. `macos-arm64` |
| `SPECWORKS_D2_CACHE` | where downloaded D2 archives are cached |

To move to a newer D2, update the version and the six hashes in `d2_release.json`.

## Project commands

Skills run the project's own tools, configured per module (a module's entries
override the top level's), in any language:

```yaml
commands:
  test: uv run pytest     # npm test, go test ./..., cargo test, ctest ...
  lint: uv run ruff check .
```

## AI tools

The skills use the open [Agent Skills](https://agentskills.io) format, so the same
files work in several tools:

| Tool | Installed files | How to run a phase |
|------|-----------------|--------------------|
| Claude Code | `.claude/skills/specworks-*/SKILL.md` | `/specworks-refine` or just ask ("let's refine ...") |
| GitHub Copilot | `.github/skills/specworks-*/SKILL.md` and `.github/prompts/specworks-*.prompt.md` | `/specworks-refine` in Copilot Chat (agent mode), or just ask |

`specworks init --tools auto` (the default) installs for the tools the project
already uses (`.claude/`, `CLAUDE.md`, `.github/copilot-instructions.md`,
`.github/prompts/`, ...) and for all of them when none is found. Use
`--tools copilot`, `--tools claude,copilot` or `--tools all` to choose.
`specworks skills` re-installs them, e.g. after upgrading specworks.

The skills call the `specworks` CLI from the terminal, so the agent needs
terminal access (Copilot agent mode, Claude Code).

## Development

```bash
uv sync
uv run pytest
uv run specworks --help
```
