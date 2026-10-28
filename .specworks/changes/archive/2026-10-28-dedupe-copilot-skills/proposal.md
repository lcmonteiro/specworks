# Proposal: dedupe-copilot-skills

## Why

`specworks init` installs skills for harnesses the user never chose, and
Copilot gets each skill two or three times (its skill, a prompt file with the
same body, and Claude Code's copy, which it also reads), so its `/` menu
repeats them. The choice is not remembered. The refinement chose Option A:
each harness declares the folders it reads, the user chooses the harnesses,
and the choice is saved.

## What Changes

- Harnesses (the `--tools` IDs, `claude` and `copilot`) each declare the skill
  folders they read and the one they prefer: Claude Code reads
  `.claude/skills/`; Copilot prefers `.github/skills/` and also reads
  `.claude/skills/` and `.agents/skills/`. Skills are written to the fewest
  folders that cover every chosen harness: Claude Code and Copilot together
  get `.claude/skills/` only.
- **BREAKING**: no Copilot prompt files (`.github/prompts/<name>.prompt.md`)
  are written any more; skills are the `/` commands. Existing `specworks-…`
  prompt files, and `specworks-…` skills in a folder the chosen harnesses no
  longer need, are removed and reported. The user's own are never touched.
- The chosen harnesses are saved as a `tools:` list in the top level's
  `.specworks/config.yml`. `init` saves its choice; `skills` and `update` save
  `--tools` when given, and, in a project with no saved choice, the
  harnesses they inferred. Without `--tools`, they use the saved choice.
- `specworks init` in a terminal, without `--tools` and with no saved choice,
  asks which harnesses the project uses, with the detected ones as the
  default. Without a terminal it uses the detected ones (`auto`), as today.
- `specworks-adopt` asks the user which harnesses the project uses and runs
  `specworks init --tools <list>` (skill text; installed copies refreshed).
- Assumptions:
  - the question takes a comma list of harness IDs, and an empty answer
    takes the default;
  - only the top level's config may set `tools:` (skills are installed at
    the workspace root); a module's config that sets it is refused;
  - `.agents/skills/` is never written by this change: no chosen harness
    prefers it yet.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `integrations`: REQ-INTEG-004 (the saved choice, `--tools` saving it),
  REQ-INTEG-005 (folders per harness, no prompt files, removing copies no
  longer needed), REQ-INTEG-006 (the skills state of the saved harnesses).
- `cli`: REQ-CLI-003 (init asks for the harnesses and saves them),
  REQ-CLI-009 (update uses and saves the choice).
- `project`: REQ-PROJ-003 (checking `tools:`), new REQ-PROJ-022 (saving
  `tools:` in the config).

## Impact

- `src/specworks/tools/skills.py` (the harness table, installing, removing,
  the skills state; `render_prompt` goes), `src/specworks/cli/project.py`
  (`init`, `skills`, `update`), `src/specworks/core/config.py` and its
  validators (the `tools` key), `specworks-adopt` skill and its installed
  copies, and the tests of all of these.
- This repository: `.github/prompts/` and `.github/skills/` copies go at the
  next `specworks skills`; `.claude/skills/` stays.

## Out of Scope

- Supporting more harnesses (Codex, Cursor): the table makes it one entry,
  but none is added here.
- Checking whether JetBrains Copilot offers skills as `/` commands (open
  question from the refinement); if it does not, those users can still ask
  for a skill by name.
- Writing skills to `.agents/skills/`.
