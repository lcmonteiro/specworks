# Refinement: add-branch-default

## Problem

`specworks new` always creates and switches to the change's own branch
unless the agent passes `--no-branch`. In a project whose branch is already
chosen (a cloud session's fixed branch, a team rule, an open PR branch) the
agent has to remember the flag on every change, and no skill mentions it:
forgetting it silently leaves the work on the wrong branch, to be switched
back and deleted by hand (this happened while developing specworks itself).

## Outcomes

- In a project set to stay on its branch, `specworks new` (and so the refine
  skill) stays on the current branch with no flag.
- A project that does not set it behaves as today: one new branch per change.
- The setting can be overridden for one change from the command line, both
  ways.
- The output says which happened: the branch created, or the branch it
  stayed on.

## Context

**Observed:**
- `src/specworks/cli/changes.py` `new`: `--no-branch` skips `plan_branch` /
  `create_branch`; the output has `branch` and `startedFrom` (both `null`
  with `--no-branch`) and a `branch  <name>` text line.
- `src/specworks/core/config.py`: `CONFIG_KEYS` lists the top-level keys;
  `diagrams:` is read from the top level only (modules' own are ignored).
  `DEFAULT_CONFIG` in `config_file.py` is the commented file `init` writes.
- `src/specworks/core/config_file.py`: `SETTABLE_KEYS` and
  `set_config_value` (add-config-set) set `context` and `commands.<key>`.
- REQ-PROJ-018 / REQ-PROJ-019 (the branch's name and where it starts),
  REQ-PROJ-003 (config value checks), REQ-PROJ-009 (default config),
  REQ-CLI-006 (creating changes), REQ-CLI-013 (`config set`).
- No skill mentions `--no-branch`; refine (and specify, when it creates a
  change) run `specworks new` without it.

**Assumed:**
- One setting for the whole workspace is enough: a git repository has one
  checked-out branch, so modules have no reason to differ.

## Constraints

- [hard] A project without the key behaves exactly as today.
- [hard] A value that is not true or false is refused when the config loads.
- [hard] Errors are values (`{"error": ...}`, exit 1 under `--json`).
- [soft] The output follows the existing `new` lines.

## Options

### Option A: a config key with flag overrides

Top-level `branch_per_change: true|false` (default true). `new` reads it;
`--branch` / `--no-branch` override it for one run. `config set
branch_per_change false` writes it. When it stays, the output names the
current branch.

- **Pros:** explicit, committed with the project, set once deterministically.
- **Cons:** one more config key.
- **Effort:** S
- **Touches:** project, cli
- **Outcomes:** meets all four.

### Option B: an environment variable

`SPECWORKS_NO_BRANCH=1` plus the flags.

- **Pros:** fits a cloud session without touching the repo.
- **Cons:** per machine; a teammate does not see it.
- **Effort:** S
- **Touches:** cli
- **Outcomes:** meets all four, only where it is set.

### Option C: skill text only

Refine tells the agent to pass `--no-branch` when the context says so.

- **Pros:** no code.
- **Cons:** still depends on the agent remembering.
- **Effort:** S
- **Touches:** skills
- **Outcomes:** meets the second and third only.

## Recommendation

Option A, agreed with the user. Out of scope: an environment variable,
changing the default, setting the key in this repository's own config,
and any change to the branch's name or start point (REQ-PROJ-018/019).

## Open Questions

- None blocking the proposal.

## Candidate Capabilities

- `project`: modified - the `branch_per_change` key (checks, default config,
  settable with `set_config_value`).
- `cli`: modified - `new` reads it with `--branch` / `--no-branch`
  overrides; `config set` accepts it.
