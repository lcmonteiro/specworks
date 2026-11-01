---
name: specworks-start
description: Start a new project with specworks from an empty repository - understand what it is, recommend its tooling, propose its structure (one simple project or several modules, each with its capabilities and code folders), and create it once the user approves the tree, then hand over to /specworks-refine for the first change. Use when the user starts a project from zero (greenfield) and wants to set it up with specworks, or says "start a project", "new project", "set up the structure" or "specworks start".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Read, Grep, Glob, Write, Edit
---

Start: set up a project that has no code yet, deciding its structure first.
It runs after `specworks init` (the step that installs this skill) and goes
on with the fresh config `init` wrote. It runs in two stages:

1. **Decide**: what the project is, its tooling, and its structure (a simple
   project or several modules, the capabilities each one owns and the
   folders that hold them), shown as a tree.
2. **Create**: once the user approves the tree, the configs, the modules,
   the capabilities and their code folders.

Then the first change starts with `/specworks-refine`. A capability gets its
spec from its first change, as ADDED requirements.

**Boundary**: starting writes only the configs, a `.gitkeep` in each
capability's code folder and (through `specworks skills`) the agent skills. No language
files: no manifest, sources or tests; the first change sets up the stack.

<!-- specworks:include running-cli -->

<!-- specworks:include asking-the-user -->

---

## Stage 1: Decide

1. **Check the repository**

   ```bash
   specworks context --json
   ```

   - `"root": null`: `specworks init` has not run here, and it is the step
     that sets up the config and installs the skills. Ask the user to run
     `specworks init` from the repository root (after `git init` when there
     is no `.git` at the root: `init` refuses outside a git repository), and
     ask "Done? (yes/no)". On yes, run this step again.
   - The project is set up already (the config is not the fresh one `init`
     writes: it has capabilities, another module, changes, or a `context`
     or `commands` filled in): refuse. Say so, and suggest
     `/specworks-refine <what you want>` for its next change (or
     `/specworks-adopt` when capabilities or commands are still missing).
     Stop here.
   - The repository already has code (source files beyond docs such as
     `README.md`, a licence, git files such as `.gitignore` and
     `.gitattributes`, and what `init` wrote): hand over to
     `/specworks-adopt`, which maps existing code. Stop here.
   - Otherwise (the fresh config `init` wrote: no capabilities, no module
     other than the top level, no changes, empty `context` and `commands`,
     in a repository with only docs, a licence and git files): go on.

2. **Understand the project**

   Ask, one question at a time, and keep each answer short:
   - what the project is and for whom (one or two sentences);
   - its stack: languages, frameworks, runtime (a service, a library, a CLI,
     a web app);
   - the AI tools it uses (saved in step 5 with `specworks skills --tools`),
     the ones the repository already shows recommended
     (`CLAUDE.md` or `.claude/` for Claude Code; `.github/copilot-instructions.md`
     for Copilot), e.g.:
     ```
     1. claude,copilot (recommended): works with both
     2. claude
     3. copilot
     ```

3. **Recommend the tooling**

   For each language of the stack, offer the build or package tool as
   numbered options, with one recommended:
   - Python: uv (recommended), over pip or poetry;
   - C++: CMake (recommended); Bazel for a large multi-language repository;
   - TypeScript: pnpm (recommended) or npm;
   - any other stack: the same rule, the stack's common build or package
     tool recommended (cargo for Rust, the go tool for Go, ...).

   The commands follow from the choice: `test`, and `lint`, `typecheck`,
   `build` or `format` when the tooling has them (for uv: `uv run pytest`,
   `uv run ruff check .`; for CMake: `ctest --test-dir build`,
   `cmake --build build`; for pnpm: `pnpm test`, `pnpm lint`).

4. **Propose the structure**

   Recommend one shape from what the user described:
   - **simple project**: one top level, its capabilities under one source
     folder (`src/<capability>`); the default for one deliverable in one
     stack;
   - **multi-module**: several modules, each a folder with its own config
     and capabilities (`services/billing`, `packages/web`); for several
     deliverables, stacks or teams in one repository.

   A capability is a durable behaviour the user would recognise, with a
   kebab-case name, a code folder and a one-line description: group by
   behaviour, not by technical layer (no `utils`, `models` or `helpers`),
   and prefer a few broad capabilities; one can be split later.

   Show the whole proposal as a plain-ASCII tree, with every module, every
   capability (name, code folder, description) and each config's context
   and commands, e.g.:
   ```
   .                                  (top level)
   |  context:  Invoicing service for small shops; Python 3.12, FastAPI.
   |  commands: test: uv run pytest   lint: uv run ruff check .
   +-- src/
       +-- invoices/   invoices   Invoice creation, numbering and PDF export
       +-- payments/   payments   Card and bank payments, refunds
   ```
   A module's context and commands are shown only when its stack differs
   from the top level's.

   Ask "Create this structure? (yes/no)". On no, apply the user's edits and
   show the tree again. **Nothing is written before a yes.**

---

## Stage 2: Create

5. **Create it**

   From the repository root, with the tools chosen in step 2:
   ```bash
   specworks skills --tools <list>
   ```
   It saves them as `tools:` in the config `init` wrote and installs the
   skills for them.

   For each module of a multi-module tree:
   ```bash
   specworks module add <path>
   ```
   It creates `<path>/.specworks/config.yml` and links it as a module named
   after its folder.

   For each capability:
   ```bash
   specworks capability add <name> --path <folder> [--module <m>] --description "<one line>"
   ```
   `--path` is relative to the module's root; `--module` names the module
   that owns it (omit it for the top level). `capability add` does not
   create the folder: write an empty `.gitkeep` in each capability's code
   folder (`<module path>/<folder>/.gitkeep`) so git keeps it.

   Write the context from the approved tree, for the top level and for a
   module whose stack differs: write it with `specworks config set context --file -` (the text on standard input).
   Write each of its commands with `specworks config set commands.<key> "<command>"`.
   For both, add `--module "<name>"` for a module's own config.
   Keep the context to a few lines (what the project is, its stack, the
   conventions a change must follow): it is read before every phase.

6. **Report and hand over**

   ```bash
   specworks context
   ```

   Show the tree as created (every module, capability and `.gitkeep`) and
   the commands written. Say that `commands.test` fails until the first
   change sets up the stack (its manifest and test runner), so that change's
   design and code gates wait for it; the first change is usually the one
   that sets up the stack. Nothing is committed: the user commits the setup.
   Then offer:
   ```
   1. /specworks-refine <first change> (recommended): explore the first change, e.g. setting up the stack
   2. Stop here
   ```

---

## Guardrails

- Only a repository with no code, right after `init`: a project already
  set up is refused, and one that already has code goes to
  `/specworks-adopt`.
- Nothing is written before the user approves the tree.
- No language files: no manifest, sources or tests, not even a test runner
  config; the first change sets up the stack.
- Only the `specworks` commands shown here, which exist today: `context`,
  `skills --tools`, `module add` and `capability add`; `init` is the user's,
  before this skill.
- Writes only the configs, the `.gitkeep` files and (through
  `specworks skills`) the agent skills; no commit.
- Never edit the living docs (`<path>/<docs_dir>/`) by hand: a capability's
  first change writes them at close.
