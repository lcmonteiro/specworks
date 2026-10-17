# 0. Set up the project

`shortlink` starts as an empty Python package with one test:

```text
src/shortlink/__init__.py
tests/test_package.py
.gitignore                 # __pycache__/, .pytest_cache/
```

On a project like this, {doc}`../skills/adopt` (stages 1 and 2) does the
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

```{literalinclude} ../example/shortlink/spec.yml
:language: yaml
:caption: spec.yml
```

Every key is described in {doc}`../reference/configuration`.

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

```{admonition} How the output feeds the skill
:class: tip feeds

- `root` is not `null`: the project is set up (otherwise the skill asks about
  `specworks init` and creates nothing by hand).
- `context`: constraints every artifact must respect ("standard library
  only"); never copied into an artifact.
- `commands.test`: the project can be tested; the design and code gates need it.
- `capabilities[].docsPath` with `hasSpec: false`: `links` has no living spec
  yet, so the first change will ADD its first requirements.
- `changes: []`: nothing in flight, so refine creates a new change.
```

The set-up is committed on `main`, and the first change is developed on a
branch (`git checkout -b add-short-links`): review compares the branch with
its base.
