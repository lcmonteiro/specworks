---
name: specworks-adopt
description: Adopt specworks in a project that already has code - set it up, find the project's test/lint commands and context, and map the existing code to capabilities (a capability's existing behaviour is then recorded with /specworks-baseline). Use when the user wants to start using specworks on an existing (brownfield) project, onboard a codebase, or says "adopt", "onboard" or "specworks adopt".
---

Adopt: bring a project that already has code into specworks, without
pretending it was built with it. It runs in two stages:

1. **Set up**: the config, the project's commands and its context.
2. **Map**: the capabilities of the existing code, registered in the config.

Then each capability in turn gets its living spec, one change per
capability:

```
/specworks-adopt
for each capability:
    /specworks-baseline <capability>
    /specworks-done baseline-<capability>     # validate, then close
```

Adopt itself never baselines: it ends by handing over to the first
`/specworks-baseline`.

**Boundary**: adopting changes no behaviour and writes only the config (and,
through `init`, the agent skills).

**Running the CLI**: use `specworks <cmd>`. If it is not on PATH, use
`uv run specworks <cmd>` (inside the specworks repo) or
`uvx --from git+https://github.com/lcmonteiro/specworks specworks <cmd>`.
Gates and `validate` reuse a test/lint/typecheck result from the same code
(`same code as the run at ...`). After fixing something outside the code (a
git-ignored file, a service the tests need), run `specworks run <key>` once:
its result replaces the reused one. `--fresh` on a gate, `start` or `validate`
does the same for that command.

---

## Stage 1: Set up

1. **Check the project**

   ```bash
   specworks context --json
   ```

   - `"root": null`: not set up yet. Look for an existing workflow-like
     folder (`spec/`, `docs/`, `openspec/`) and ask the user for the folder
     name (`--dir`, default `specworks`); it also names the config file and
     cannot change without renaming both. Then, with their go-ahead:
     ```bash
     specworks init --dir <dir>
     ```
   - Already set up: say so, and continue with whatever is still missing
     (empty `commands`, empty `context`, no capabilities). Never overwrite
     what the user wrote.
   - Several independent projects in one repository (each with its own
     build file: `services/*/pyproject.toml`, a `packages/*/package.json`
     workspace, ...): propose one module per project and, once confirmed,
     `specworks module add <path>` for each. Run stages 1-2 in each module
     from its folder.

2. **Find the project's commands**

   Read, without running anything yet: `pyproject.toml`, `package.json`
   scripts, `Makefile`, `Cargo.toml`, `go.mod`, `CMakeLists.txt`, `tox.ini`,
   `noxfile.py`, the CI workflows (`.github/workflows/*.yml`, `.gitlab-ci.yml`)
   and the README's development section. CI is the best evidence: it shows
   the commands the project really runs.

   Propose `test`, and `lint` / `typecheck` / `build` when the project has
   them, in a short table with where each one came from. Once confirmed, write
   them under `commands:` in the config (`<dir>.yml` in the module's folder,
   `dir` in `specworks context --json`), then run each one:
   ```bash
   specworks run test
   specworks run lint
   ```
   A failing command is the project's starting state, not something to fix
   here: report it, and tell the user that the design and code gates need
   `commands.test` to pass.

3. **Write the context**

   From the README, `CLAUDE.md` / `AGENTS.md` / `.github/copilot-instructions.md`,
   the contributing guide and the dependencies: a few lines on what the
   project is, its stack, and the conventions a change must follow (style,
   error handling, layering, what not to touch). Show it, apply corrections,
   and write it under `context:` in the config. Keep it short: it is read
   before every phase. Point to those files rather than copying them.

4. **Choose the files to scan for tags** (only when needed)

   Empty `test_globs` / `source_globs` scan every file outside the workflow
   folder. Set them when that would pick up generated code, vendored code or
   fixtures (`vendor/`, `dist/`, `node_modules/`, snapshot files):
   `test_globs: ["tests/**/*.py"]`, `source_globs: ["src/**"]`.

---

## Stage 2: Map the capabilities

5. **Propose capabilities**

   A capability is a durable behaviour of the system that owns a code folder
   (`user-auth` → `src/auth`); its living docs go to `<path>/<docs_dir>/`.
   Read the layout, the entry points (routes, CLI commands, public modules)
   and the tests' folder structure, and propose a table:

   ```
   Capability    Path            Prefix    Description
   user-auth     src/auth        AUTH      Login, sessions and password reset
   invoices      src/billing     INVOICES  Invoice creation, numbering and PDF export
   ```

   - Group by behaviour the user would recognise, not by technical layer: no
     `utils`, `models` or `helpers` capability.
   - Prefer a few broad capabilities to many small ones; one can be split
     later.
   - Each capability needs its own prefix; keep them short and readable.
   - Code that is pure plumbing (build scripts, generated code) needs no
     capability.

   Ask the user to confirm or edit the table. **Stop and wait.**

6. **Register them**

   For every confirmed row:
   ```bash
   specworks capability add <name> --path <path> [--prefix <P>] [--description "<one line>"]
   ```
   Then check the result:
   ```bash
   specworks spec list
   ```

7. **Report and stop**

   Summarize: the config file, the commands and whether each passes, the
   context written, the modules and the capabilities. Then:

   "specworks is set up. Next, each capability gets its living spec, one
   at a time: run `/specworks-baseline <first capability>`, then
   `/specworks-done baseline-<first capability>`, and so on for the
   others (in the order of the table). A baseline records the behaviour the
   capability already has, so later changes can MODIFY its requirements
   instead of only ADDING them."

   **End here.** The baselines are `/specworks-baseline`, one capability
   per run.

---

## Guardrails

- Stop after stage 2: a baseline is `/specworks-baseline`, never part of
  adopt.
- Never change behaviour while adopting: no refactors, no bug fixes, no
  renames. A failing command or a bug is reported, not fixed.
- The user confirms the commands and the capability table before they are
  written into the project.
- Capability names and prefixes are checked with the CLI (`spec list`),
  never assumed.
- Never edit the living docs (`<path>/<docs_dir>/`) by hand: `close` writes
  them.
