# 0. Set up the project

`shortlink` starts as an empty Python package with one test:

```text
src/shortlink/__init__.py
tests/test_package.py
.gitignore                 # __pycache__/, .pytest_cache/
```

On a project like this, [/specworks-adopt](Skills-Adopt) (stages 1 and 2) does the
set-up. These are the commands it runs.

## Initialise

```console
$ specworks init --dir spec --tools claude
created spec.yml
ready   spec/changes/
tools   Claude Code
skill   .claude/skills/specworks-adopt/SKILL.md
skill   .claude/skills/specworks-build/SKILL.md
skill   .claude/skills/specworks-close/SKILL.md
skill   .claude/skills/specworks-code/SKILL.md
skill   .claude/skills/specworks-design/SKILL.md
skill   .claude/skills/specworks-refine/SKILL.md
skill   .claude/skills/specworks-review/SKILL.md
skill   .claude/skills/specworks-specify/SKILL.md
skill   .claude/skills/specworks-test/SKILL.md
skill   .claude/skills/specworks-validate/SKILL.md
```

## Configure

`spec.yml` comes with comments explaining every key. Adopt proposes `commands`
from the build files and CI, and `context` from the README; you confirm them.
The result for `shortlink`:

[`spec.yml`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/spec.yml):

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

Every key is described in [Configuration: `<dir>.yml`](Reference-Configuration).

## Register the capability

```console
$ specworks capability add links --path src/shortlink --prefix LINK --description "Create short codes for URLs and resolve them"
registered links -> src/shortlink (REQ-LINK-)
```

## Record the starting state

Adopt runs each configured command once. A failing command is the project's
starting state: reported, not fixed.

```console
$ specworks run test
.                                                                        [100%]
1 passed in 0.00s
$ specworks run lint
All checks passed!
$ specworks spec list
links                        REQ-LINK-  0 req  src/shortlink/docs/spec.md
```

## What every skill reads first

`specworks context --json` is the first command of every skill:

```json
{
  "root": "/work/shortlink",
  "module": "(top)",
  "dir": "spec",
  "changesDir": "spec/changes",
  "context": "Python 3.12 library, standard library only. Public API lives in src/shortlink/.\nErrors are raised as subclasses of shortlink.errors.ShortlinkError.",
  "contextChain": [
    {
      "module": "(top)",
      "context": "Python 3.12 library, standard library only. Public API lives in src/shortlink/.\nErrors are raised as subclasses of shortlink.errors.ShortlinkError."
    }
  ],
  "commands": {
    "test": "python -m pytest -q -p no:cacheprovider -o pythonpath=src tests",
    "lint": "ruff check src tests"
  },
  "modules": [
    { "name": "(top)", "path": ".", "dir": "spec", "changesDir": "spec/changes", "current": true }
  ],
  "missingModules": [],
  "capabilities": [
    {
      "name": "links",
      "module": "(top)",
      "path": "src/shortlink",
      "description": "Create short codes for URLs and resolve them",
      "docsPath": "src/shortlink/docs",
      "hasSpec": false,
      "prefix": "LINK",
      "deltaPath": "specs/links/spec.md"
    }
  ],
  "changes": []
}
```

> [!TIP]
> **How the output feeds the skill**
>
> - `root` is not `null`: the project is set up (otherwise the skill asks about
>   `specworks init` and creates nothing by hand).
> - `context`: constraints every artifact must respect ("standard library
>   only"); never copied into an artifact.
> - `commands.test`: the project can be tested; the design and code gates need it.
> - `capabilities[].docsPath` with `hasSpec: false`: `links` has no living spec
>   yet, so the first change will ADD its first requirements.
> - `changes: []`: nothing in flight, so refine creates a new change.

The set-up is committed on `main`, and the first change is developed on a
branch (`git checkout -b add-short-links`): review compares the branch with
its base.
