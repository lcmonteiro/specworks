# Configuration: `<dir>.yml`

The config file is named after the workflow folder: `specworks init --dir spec`
creates `spec.yml` and `spec/`. Every module uses the same name. To rename
later, rename both the file and the folder. Unknown keys are an error, so a
typo never passes silently.

```{literalinclude} ../example/shortlink/spec.yml
:language: yaml
:caption: spec.yml of the tutorial project
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
{ref}`specworks capability add <cmd-capability>`.

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
test files recognised by folder and name ({doc}`../concepts/ids-and-tags`). In
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
| `SPECWORKS_RUN_CACHE=0` | never reuse a project command's result ({doc}`run-cache`) |
