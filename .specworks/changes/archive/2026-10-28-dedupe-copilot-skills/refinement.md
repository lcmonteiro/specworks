# Refinement: dedupe-copilot-skills

## Problem

`specworks init` installs skills for harnesses the user never chose (with
nothing detected it installs for every tool), and for Copilot it writes each
skill twice: a skill in `.github/skills/` and a prompt file with the same body
in `.github/prompts/`. Copilot now offers skills as `/` commands and also reads
`.claude/skills/`, so in a project with both tools Copilot can list each
specworks skill two or three times, and `specworks skills` keeps all those
copies in sync. The choice of harnesses is not remembered: `update` guesses it
from the folders on disk. (Source: user question in session, paraphrased;
VS Code "Use Agent Skills" and GitHub "About agent skills" docs.)

## Outcomes

- In a terminal, `specworks init` asks which harnesses the project uses
  (Claude Code, Copilot, ...), with the detected ones preselected. Without a
  terminal (CI, `--json`, an agent) it uses the detected ones, as `auto` does
  today, and `--tools` skips the question.
- `/specworks-adopt` asks the user which harnesses the project uses and
  passes them to `specworks init` with `--tools`.
- The choice is saved in `.specworks/config.yml`; `specworks skills` and
  `specworks update` install for exactly those harnesses. A project with no
  saved choice behaves as today.
- Each chosen harness shows each specworks skill once in its `/` menu. With
  Claude Code and Copilot chosen together, the skills are only in
  `.claude/skills/`. No Copilot prompt file is written.
- On upgrade, the `specworks-…` copies a project no longer needs (prompt files
  in `.github/prompts/`, and `.github/skills/` when Claude Code is also chosen)
  are removed, each reported; the user's own skills and prompt files are kept.
- The skills state is `current` right after `specworks skills`, with no prompt
  files expected.

## Context

**Observed:**
- `src/specworks/tools/skills.py`: `TOOLS` has `claude` (`.claude/skills`) and
  `copilot` (`.github/skills` plus `prompts_dir=".github/prompts"`, keeping
  only `name` and `description`); `render_prompt` writes the prompt files;
  `parse_tools` handles `auto` / `all` / a list; `installed_tools` infers the
  tools from the folders that hold a `specworks-…` skill; stale removal and
  the skills state already cover prompt files.
- `src/specworks/cli/project.py`: `init`, `skills` and `update` take `--tools`
  (`ToolsOpt`, default `auto`); `update` without `--tools` uses
  `installed_tools`. Nothing is asked and nothing is saved in the config.
- `src/specworks/skills/specworks-adopt/SKILL.md` step 1 runs `specworks init`
  from the agent, with no terminal.
- Living spec `src/specworks/tools/docs/spec.md`: REQ-INTEG-004 (choosing the
  tools), REQ-INTEG-005 (installing, prompt files, stale removal),
  REQ-INTEG-006 (skills state).
- VS Code docs: project skills are read from `.github/skills/`,
  `.claude/skills/` and `.agents/skills/`; "By default, all skills appear in
  the `/` menu"; a skill with the same name in two locations appears twice.
  GitHub docs list the same three project folders for Copilot.

**Assumed:**
- Copilot ignores the `allowed-tools` key in Claude's copy (the Agent Skills
  standard lists it as optional). Not tested.
- Once the skills are slash commands, the prompt files add nothing; not
  checked for JetBrains Copilot (skills in public preview there).

## Constraints

- [hard] Never ask without a terminal: `--json`, CI and agents get the
  detected harnesses, never a hanging prompt.
- [hard] `--tools auto|all|<list>` keeps working on `init`, `skills` and
  `update`.
- [hard] Only `specworks-…` (and `sw-refine`) skills and prompt files are
  ever removed; the user's own are never touched.
- [hard] Config and skill files are read and written with `encoding="utf-8"`.
- [soft] Adding a harness later (Codex through `.agents/skills/`) is a table
  entry, not new logic.

## Options

### Option A: Each harness declares the folders it reads

Each `Tool` lists the skill folders it reads and the one it prefers (Claude
Code: `.claude/skills`; Copilot: `.github/skills`, `.claude/skills`,
`.agents/skills`). The installer writes to the fewest folders that cover every
chosen harness (Claude Code + Copilot → `.claude/skills/` only). Prompt files
go. The choice is saved as a `tools:` list in `config.yml`, read by `skills`
and `update`; `init` asks with a checklist in a terminal.

- **Pros:** one rule for every combination; a new harness is one entry.
- **Cons:** the installed folders no longer map one-to-one to the harnesses,
  so the saved choice (not the folders) is what `update` and the skills state
  rely on.
- **Effort:** M
- **Touches:** `integrations`, `cli`, `project`
- **Outcomes:** meets all six.

### Option B: A special case for Claude Code + Copilot

Same saved choice and question; the installer skips Copilot's folder when
Claude Code is chosen.

- **Pros:** slightly less code today.
- **Cons:** every new harness needs another special case.
- **Effort:** S-M
- **Touches:** `integrations`, `cli`, `project`
- **Outcomes:** meets all six today; fails the soft constraint on new harnesses.

## Recommendation

Option A, agreed with the user: about the same effort as B, and new harnesses
fit without special cases.

## Open Questions

- Does Copilot in JetBrains offer skills as `/` commands? If not, JetBrains
  users lose the slash command with the prompt files. Not blocking.
  (who can answer: maintainer, by trying it)
- Does `--tools` on `skills` or `update` also change the saved choice, or
  apply to that run only? Not blocking; specify decides. (who can answer:
  maintainer)

## Candidate Capabilities

- `integrations`: modified - harnesses declare the folders they read; no
  prompt files; stale copies removed; skills state from the saved choice
- `cli`: modified - `init` asks for the harnesses in a terminal
- `project`: modified - `tools:` list in `.specworks/config.yml`
