# Refinement: add-start-skill

## Problem

Someone starting a repository from zero has no guided path into specworks.
`/specworks-adopt` covers a project that already has code, and
`/specworks-refine` starts a change, but nothing helps decide the structure
first: one simple project or several modules, which capabilities each one
owns, and which folders hold them. Today that means working it out alone,
running `specworks init`, `specworks module add` and `specworks capability
add` one by one, and creating the code folders by hand. (Source: user
request in session, paraphrased.)

## Outcomes

- In an empty git repository, `/specworks-start` asks what the project is,
  its stack and the AI tools it uses; it recommends a simple project (one top
  level) or a multi-module one (modules, each with its capabilities), and
  shows the proposed tree before anything is written.
- Once the user approves the tree, every module is linked, every capability
  is registered with its code folder created (with a `.gitkeep`), and
  `specworks context` lists them all.
- The config holds a short project context with the chosen stack and
  tooling, which the skill recommends as numbered options (uv for Python;
  CMake, or Bazel for large multi-language repos, for C++; pnpm or npm for
  TypeScript), and the test / lint / build commands for that tooling.
- It ends by handing over to `/specworks-refine` for the first change.

## Context

**Observed:**
- Tried in an empty repository: `specworks init` sets up the top level;
  `specworks module add services/billing` creates
  `services/billing/.specworks/config.yml` and links it as `billing`;
  `specworks capability add <name> --path <folder>` registers a capability
  in the current module but does not create its folder; `specworks context`
  then lists every capability with `hasSpec: false` (its spec comes from its
  first change, as ADDED requirements).
- `src/specworks/skills/specworks-adopt/SKILL.md`: the brownfield path. It
  asks the AI tools and passes `--tools` to init (init cannot ask from an
  agent), proposes and writes `commands:` and `context:` in the config, and
  registers capabilities; its steps are the model for the new skill.
- `config.yml` `commands:` accepts `test`, `lint`, `typecheck`, `build`,
  `format` (REQ-PROJ-003).
- The README lists the skills; `tests/test_skills.py` checks every packaged
  skill (frontmatter, CLI calls that exist, shared parts filled in).

**Assumed:**
- With no test runner yet, `commands.test` fails until the first change sets
  up the stack, so the design and code gates of that change wait for it.
  The hand-over should say so.

## Constraints

- [hard] Runs only in a git repository with no specworks config; a project
  that already has code is handed over to `/specworks-adopt`, and one with a
  config is refused.
- [hard] Nothing is written until the user approves the tree.
- [hard] No language files: no manifest, sources or tests.
- [hard] Only commands that exist today (`init`, `module add`,
  `capability add`, `context`); `tests/test_skills.py` checks the calls.
- [soft] Empty folders get a `.gitkeep` so git keeps them.

## Options

### Option A: A new skill on today's commands

`specworks-start` runs `init --tools`, `module add` and `capability add`,
creates each capability's folder with a `.gitkeep`, and writes the context
and commands in the config, as adopt does.

- **Pros:** everything it needs exists; no CLI change.
- **Cons:** folder creation is done by the agent, not tested by the CLI.
- **Effort:** S-M
- **Touches:** none (a packaged skill)
- **Outcomes:** meets all four.

### Option B: A plus `capability add --create`

The CLI creates the code folder (with a `.gitkeep`) when it registers the
capability.

- **Pros:** folder creation is the same on every OS, and tested.
- **Cons:** a behaviour change in `cli` with its own requirement.
- **Effort:** M
- **Touches:** `cli`, `project`
- **Outcomes:** meets all four.

### Option C: A structure file

The skill writes the tree to a file and `specworks init --plan
structure.yml` creates everything from it.

- **Pros:** the tree is reviewable as a file; one command builds it.
- **Cons:** a new file format and command to specify and keep compatible.
- **Effort:** L
- **Touches:** `cli`, `project`
- **Outcomes:** meets all four.

## Recommendation

Option A, agreed with the user: everything it needs exists, and folder
creation is two lines of skill text.

## Open Questions

- Is `specworks-start` the right name? Not blocking. (who can answer:
  maintainer)
- Is `capability add --create` (Option B) worth adding later? Not blocking.
  (who can answer: maintainer)

## Candidate Capabilities

- None: a packaged skill (skills have no capability), plus the README line.
