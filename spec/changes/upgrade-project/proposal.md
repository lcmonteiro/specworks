# Proposal: upgrade-project

## Why

After `uv tool upgrade specworks`, a project's installed agent skills stay at
the old version, and nothing says so. The refinement chose a two-step upgrade
(Option A): uv upgrades the CLI, then `specworks update` brings the project up
to that CLI. Staleness is found by comparing the installed skills with what
this CLI would install, because the version (`0.1.0`) is never bumped.

## What Changes

- **Skills state:** specworks compares the skills it would install with the
  ones installed, for each tool that has specworks skills. The state is:
  - `current`;
  - `outdated`, with each differing, missing or no-longer-shipped file;
  - `none`, when no specworks skill is installed.
- **New command `specworks update`:**
  - refreshes the skills of the tools that have them installed (`--tools`
    overrides this; with none installed it falls back to `auto`, like
    `specworks skills`);
  - writes only the files that differ and removes the stale ones, printing
    `updated <path>` and `removed <path>`;
  - prints `skills up to date` when nothing changed;
  - works from any module, on the workspace root.
- **`specworks context`:** shows the skills state, `skills` in `--json`. When
  outdated, it also shows the hint `skills out of date: run specworks update`.
- **README:** a short "Upgrade" part with `uv tool upgrade specworks` and
  `specworks update`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `integrations`: ADDED REQ-INTEG-006, the skills state.
- `cli`:
  - ADDED REQ-CLI-009, `update`;
  - MODIFIED REQ-CLI-004, `context` shows the skills state.

## Impact

- `src/specworks/tools/skills.py`: comparing the skills, and writing only the
  files that differ.
- `src/specworks/cli/project.py`: the `update` command and the skills state
  in `context`.
- `README.md`: the Upgrade part.
- No config or data format change. `specworks skills` keeps its behaviour.

## Out of Scope

- Upgrading the CLI itself: `uv tool upgrade specworks` does that (Option B
  was not chosen).
- Config migration: there is only one config format. A config whose format
  the CLI does not know is already refused with "unsupported config version
  specworks: N (expected 1)". `update` is where a migration will run once a
  second format exists.
- A version stamp in the config.
- Keeping a user's hand edits to an installed skill: `update` overwrites them,
  as `specworks skills` does.
