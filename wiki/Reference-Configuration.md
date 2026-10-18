# Configuration: `<dir>.yml`

The config file is named after the workflow folder: `specworks init --dir spec`
creates `spec.yml` and `spec/`. Every module uses the same name. To rename
later, rename both the file and the folder. Unknown keys are an error, so a
typo never passes silently.

[`spec.yml of the tutorial project`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/spec.yml):

<!-- include: examples/shortlink/spec.yml -->
```yaml
specworks: 1
# specworks configuration. The file name sets the workflow folder:
# spec.yml -> spec/changes/ (in-flight changes) and spec/changes/archive/.
# Modules (sub-projects) use the same file and folder name as the top level.
#
# context: free text the agent reads before every phase (stack, conventions,
# constraints). Keep it short; it is guidance, not documentation.
context: |
  Python 3.12 library, standard library only. Public API lives in src/shortlink/.
  Errors are raised as subclasses of shortlink.errors.ShortlinkError.

# Name of the folder, inside each capability's code path, that holds its
# living docs (spec.md, requirements.md, design.md, architecture.md).
docs_dir: docs

# Capabilities: durable behaviours of the system and the code folder that owns
# each one. `close` writes the capability's living docs into <path>/<docs_dir>/.
# Requirement IDs are REQ-<prefix>-NNN; the prefix defaults to the capability
# name in upper case (with the module name in front inside a module).
# capabilities:
#   user-auth:
#     path: src/auth
#     description: Login, sessions and password reset
#     prefix: AUTH          # optional: REQ-AUTH-001 instead of REQ-USER-AUTH-001
capabilities:
  links:
    path: src/shortlink
    description: "Create short codes for URLs and resolve them"
    prefix: LINK

# Modules: sub-projects with their own config (same file name as this one),
# like git submodules. Each one is a complete project (own context,
# capabilities and changes) linked to this one. Add them with `specworks module add <path>`.
# modules:
#   billing: services/billing
modules: {}

# Globs used by `specworks trace` to find tests and source files, relative to
# this file's folder; they apply to this project's files, not to its modules'.
# Empty means "scan everything that is not in the workflow folder", except
# documentation (.md, .rst, .txt, ...): a tag quoted in a doc is not code or a test.
# In a glob * and ? stay within one folder and ** spans any number of folders,
# e.g. test_globs: ["tests/**/*.py"] or source_globs: ["src/**"].
test_globs: []
source_globs: []

# Commands the skills run, in this project's own tooling (any language).
# A module's commands override the top level's, key by key.
#   test: uv run pytest            # or: npm test, go test ./..., cargo test, ctest
#   lint: uv run ruff check .
commands:
  test: python -m pytest -q -p no:cacheprovider -o pythonpath=src tests
  lint: ruff check src tests

# Design diagrams are written in D2 (https://d2lang.com) and rendered to SVG
# by `specworks diagrams`. Only the top-level settings are used, so every
# diagram in the workspace shares one look (modules ignore theirs).
# Themes by name or number - `specworks diagrams --themes` lists them, e.g.
# neutral-default, neutral-grey, cool-classics, colorblind-clear, c4, origami;
# dark mode: dark-mauve, dark-flagship-terrastruct, or none (same as theme).
diagrams:
  theme: neutral-default
  dark_theme: dark-mauve
  layout: elk           # elk or dagre
  sketch: false         # true for a hand-drawn look
```

## Keys

| Key | Type | Default | Meaning |
|---|---|---|---|
| `specworks` | `1` | (required) | marks the file as a specworks config, version 1 |
| `context` | text | empty | what the agent reads before every phase: stack, conventions, constraints. Short guidance, not documentation. A module's context is added after its parents' |
| `docs_dir` | path | `docs` | folder, inside each capability's code path, holding its living docs |
| `capabilities` | mapping | `{}` | `name: {path, prefix?, description?}` |
| `modules` | mapping | `{}` | `name: folder` of linked sub-projects (`specworks module add`) |
| `test_globs` | list | `[]` | files scanned for `@ac` tags and treated as tests, relative to the config's folder |
| `source_globs` | list | `[]` | files scanned for `@req` tags |
| `commands` | mapping | `{}` | the project's commands: `test`, `lint`, `typecheck`, `build`, `format` |
| `diagrams` | mapping | see below | D2 rendering settings (only the top level's are used) |

### `capabilities`

```yaml
capabilities:
  links:
    path: src/shortlink          # code folder that owns it (required)
    prefix: LINK                 # REQ-LINK-NNN; default: the name in upper case
    description: Create short codes for URLs and resolve them
```

Inside a module, the default prefix has the module name in front. Two
capabilities with the same prefix are a config error. Add them with
[specworks capability add](CLI-Specs#specworks-capability-add).

### `commands`

```yaml
commands:
  test: uv run pytest          # npm test, go test ./..., cargo test, ctest ...
  lint: uv run ruff check .
  typecheck: uv run mypy
  build: uv build
```

Run in the module's folder, by `specworks run <key>` and by the gates (`test`
by design, code and review; `build` and `typecheck` by design when set; `test`,
`lint` and `typecheck` by validate). A module's entries override the top
level's, key by key.

### `test_globs` / `source_globs`

```yaml
test_globs: ["tests/**/*.py"]
source_globs: ["src/**"]
```

Empty means "scan every file outside the workflow folder, except docs", with
test files recognised by folder and name ([IDs, tags and traceability](Concepts-IDs-and-Tags)). In
a glob `*` and `?` stay within one folder and `**` spans any number of folders;
`[..]` and `{..}` are rejected. A single string instead of a list is an error.

### `diagrams`

```yaml
diagrams:
  theme: neutral-default   # by name or number: c4, colorblind-clear, cool-classics, origami, ...
  dark_theme: dark-mauve   # used in dark mode; dark-flagship-terrastruct, or none
  layout: elk              # or dagre
  sketch: false            # true for a hand-drawn look
  pad: 24                  # padding around the diagram, in pixels
```

`specworks diagrams --themes` lists the themes. Changing a setting marks every
SVG outdated until `specworks diagrams` renders it again.

## Environment variables

| Variable | Effect |
|---|---|
| `SPECWORKS_D2` | use this `d2` instead of the one from `pyd2` |
| `SPECWORKS_RUN_CACHE=0` | never reuse a project command's result ([The run cache](Reference-Run-Cache)) |
