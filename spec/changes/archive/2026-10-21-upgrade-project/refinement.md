# Refinement: upgrade-project

## Problem

A project that uses specworks has no clear way to catch up with a newer
specworks. The user's words: "I need a way to upgrade a project that uses
specworks", sketched as "uv update ...; uv specworks update ...". The CLI
upgrades through uv, but the project's installed agent skills stay as they
were. Nothing says they are out of date, and the only hint is a passing
"e.g. after upgrading specworks" in the README.

## Context

**Observed:**
- Install: `uv tool install git+https://github.com/lcmonteiro/specworks`
  (README "Install"). `uv tool upgrade specworks` already upgrades the CLI.
- `specworks skills` (`src/specworks/cli/project.py`, `write_skills`):
  - installs the skills for `--tools` (default `auto`, the tools the project
    already uses: `parse_tools` in `src/specworks/tools/skills.py`);
  - first removes the skills a newer version renamed or dropped
    (`remove_stale_skills`);
  - then writes every packaged skill (`install_skills`), overwriting the
    installed copies.
- The version is `0.1.0` (`pyproject.toml`, `specworks.__version__`), and
  installs come straight from git, so the version does not change between
  upgrades.
- The config's `specworks: 1` is its format version. A different value is
  refused with "unsupported config version" (`core/config.py`). There is no
  migration, and only one format exists.
- `specworks context --json`, which every skill runs first, reports the
  workspace state. It does not say anything about the skills.
- Capabilities involved: `integrations` (installing the agent skills) and
  `cli` (the command surface).

**Assumed:**
- Rendering the packaged skills and comparing them with the installed files
  is cheap enough to do on every `context` call (12 small files per tool).

## Constraints

- [hard] The upgrade has two steps: `uv tool upgrade specworks` upgrades the
  CLI (specworks does not upgrade itself), then `specworks update` brings the
  project up to that CLI.
- [hard] Staleness is decided by comparing the installed skills with what
  this CLI would install, not by a version number (which is never bumped).
- [hard] `update` covers the whole workspace (the skills live at its root),
  and by default keeps the tools already installed.
- [soft] `specworks skills` stays; `update` reuses it for the skills.
- [soft] The README gets an "Upgrade" part with the two commands.

## Options

### Option A: uv upgrade + `specworks update`, skills compared (chosen)

- `specworks update` refreshes the skills, as `specworks skills` does, and
  reports what changed: written, removed, already up to date.
- `specworks context` adds a skills state (e.g. `"skills": "outdated"`, with
  the differing files) and a one-line hint: "skills out of date: run
  `specworks update`".
- A config with an unsupported format version gets a clear message that
  names the CLI's expected version.

- **Pros:** matches the user's sketch, and the version needs no bumping. It
  also catches a hand-edited or deleted skill. Agents see the hint through
  `context`.
- **Cons:** a hand-edited skill shows as out of date, and `update` overwrites
  it, as `specworks skills` does today.
- **Effort:** M.
- **Touches:** `integrations`, `cli`.

### Option B: one `specworks upgrade`

The command also runs `uv tool upgrade specworks` when uv installed the CLI,
then updates the project.

- **Pros:** one command.
- **Cons:** the CLI has to detect how it was installed and replace itself
  while it runs.
- **Effort:** L.
- **Touches:** `integrations`, `cli`.

### Option C: warning only

Record or compare the skills, and warn "run `specworks skills`". No new
command.

- **Pros:** the smallest change.
- **Cons:** no single upgrade step to grow into, e.g. config migration.
- **Effort:** S.
- **Touches:** `integrations`, `cli`.

## Recommendation

Option A, chosen by the user: `uv tool upgrade specworks`, then
`specworks update`, with staleness found by comparing the installed skills.
Config migration is out of scope until a second config format exists; then
`update` is where it runs.

## Open Questions

- Should `update` also run when the config format is newer than the CLI (a
  teammate on a newer specworks)? The likely answer is to refuse, and tell
  them to upgrade the CLI first. The specify phase can confirm this with the
  user.

## Candidate Capabilities

- `integrations`: modified. Skills are compared with the installed copies,
  and the update reports what it changed.
- `cli`: modified. The new `specworks update` command, and the skills state
  in `context`.
