# Proposal: add-start-skill

## Why

A repository started from zero has no guided path into specworks: the user
decides the structure alone, runs `init`, `module add` and `capability add`
one by one, and creates the code folders by hand. The refinement chose
Option A: a new skill, `specworks-start`, on today's commands.

## What Changes

- New packaged skill `src/specworks/skills/specworks-start/SKILL.md`
  (with the shared `running-cli` and `asking-the-user` parts), in the shape
  of `specworks-adopt`:
  1. **Check the repository**: `specworks context --json`. Start runs after
     `specworks init`, the step that installs the skills, so it goes on with
     the fresh config `init` wrote (no capabilities, no other module, no
     changes, empty `context` and `commands`). A project already set up is
     refused (use `/specworks-refine`); a repository that already has code
     (source files beyond docs, licence and git files) is handed over to
     `/specworks-adopt`; `"root": null` means `init` has not run: say to run
     `specworks init` (and `git init` first when there is no repository).
     (review R1)
  2. **Understand the project**: what it is, for whom, its stack, and the AI
     tools it uses, one question at a time.
  3. **Recommend the tooling**: for the stack, numbered options with one
     recommended: uv for Python (over pip, poetry); CMake for C++ (Bazel for
     large multi-language repos); pnpm or npm for TypeScript; others by the
     same rule (the stack's common build or package tool). The test / lint /
     build commands follow from the choice (e.g. `uv run pytest`,
     `uv run ruff check .`).
  4. **Propose the structure**: a simple project (one top level, capabilities
     under one source folder) or a multi-module one (modules, each a folder
     with its own capabilities), recommended from what the user described;
     shown as a plain-ASCII tree with every module, capability (kebab-case
     name, code folder, one-line description) and the config's context and
     commands. Ask "Create this structure? (yes/no)"; nothing is written
     before a yes.
  5. **Create it**: `specworks skills --tools <list>` (saves the AI tools
     chosen in step 2 and installs the skills for them); `specworks module add
     <path>` per module; `specworks capability add <name> --path <folder>
     [--module <m>] --description "<line>"` per capability; a `.gitkeep` in
     each capability's code folder; `context:` and `commands:` written in
     each config (the top level's, and each module's when its stack
     differs).
  6. **Report and hand over**: `specworks context`, the tree as created, a
     note that `commands.test` fails until the first change sets up the
     stack (so its design and code gates wait for it), and the next step:
     `/specworks-refine <first change>` (recommended), or stop here.
  - Guardrails: no language files (no manifest, sources or tests); only
    `specworks-…` commands that exist; writes only the configs, the
    `.gitkeep` files and (through `specworks skills`) the agent skills; no commit, as in
    adopt.
- `README.md`: after `specworks init`, the steps list `/specworks-start` for
  a repository with no code yet, next to `/specworks-adopt` for a project
  with code (review R1).
- `tests/test_skills.py`: wording checks for the new skill, and
  `specworks-start` joins the skills that create their project instead of
  picking a change. Installed copies refreshed with `specworks skills`.
- Assumption: "already has code" is the agent's reading of the files; no
  CLI check.

## Capabilities

None: a packaged skill and the README; the change is marked `skip-specs`.

### New Capabilities

- None.

### Modified Capabilities

- None.

## Impact

- New `src/specworks/skills/specworks-start/` and its installed copy in
  `.claude/skills/`, `README.md`, `tests/test_skills.py`. No CLI change.

## Out of Scope

- Language scaffolding (manifest, test runner, sources).
- `capability add --create` and a structure file for `init` (the
  refinement's Options B and C).
- Changing `specworks-adopt`.
