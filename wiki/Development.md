# Development

## Set up and check

```console
$ uv sync
$ uv run pytest
$ uv run ruff check src tests     # lint
$ uv run mypy                     # typecheck
$ uv run coverage run -m pytest && uv run coverage report   # branch coverage; CI fails under 95%
$ uv run specworks --help
```

## Edit this documentation

The documentation is this wiki. Its pages live in the main repository, in
`wiki/`, so a change to the docs goes through a pull request like any other
change, and the wiki is overwritten from `wiki/` on every push to `main` (by the
`Wiki` workflow, `.github/workflows/wiki.yml`). Edits made in the wiki's web
editor are lost on the next push: make them in `wiki/` instead.

| Path | What |
|---|---|
| `wiki/<Page-Name>.md` | one page; the file name is the page name, and links between pages use it: `[Phases and gates](Concepts-Phases)` |
| `wiki/_Sidebar.md` | the navigation on the right of every page |
| `wiki/images/` | images, linked as `images/<file>` |
| `examples/shortlink/` | the tutorial's project, as it is at the end |

A file the pages show (a `SKILL.md`, `schema.yaml`, a template, a file of the
example project) is copied into the page after a marker:

    <!-- include: src/specworks/schema.yaml -->
    ```yaml
    ...
    ```

`tests/test_wiki.py` fails when the copy no longer matches the file, when a
link points at a page that does not exist, or when a page is missing from the
sidebar. To refresh every copy after editing a skill or a template:

```console
$ uv run python tests/test_wiki.py --update
```

Command output in the tutorial and the CLI reference was captured by running
specworks on the example project. When a command's output changes, run it
again in a copy of `examples/shortlink/` and update the page.

The wiki must exist before the first publish: create any page once in the
repository's **Wiki** tab (the workflow then replaces it).

## Code layout

| Package | What it holds |
|---|---|
| `cli/` | the `specworks` command: `app.py` (Typer app and command groups), `output.py` (options, JSON/text output, resolving changes), and one module per area: `project.py`, `changes.py`, `specs.py`, `workflow.py` |
| `core/` | `config.py`, `config_file.py`, `workspace.py`, `changes.py`, `runner.py`, `git.py`, `files.py`, `validators.py`, `errors.py` (`SpecworksError`, the base of every error the CLI reports) |
| `specs/` | `specfile.py`, `capabilities.py`, `check.py`, `tasks.py`, `trace.py`, `merge.py` |
| `workflow/` | `artifacts.py`, `checks.py` (gates and validate are lists of these checks), `gate.py`, `review.py`, `cycle.py`, `validate.py` |
| `tools/` | `diagrams.py`, `skills.py` |

`schema.yaml`, `templates/` and `skills/` are package data next to them. Text
several skills share lives once in `skills/_shared/<name>.md`; a skill marks
its place with `<!-- specworks:include <name> -->`, filled in on install.

## Updating pyd2 (and D2)

`pyproject.toml` pins `pyd2` to one commit, so `uv sync`, CI and
`uv tool install git+https://github.com/lcmonteiro/specworks` (which does not
read `uv.lock`) all build the same D2. To take a newer one, put its commit in
`pyproject.toml`, then:

```console
$ uv lock
$ uv run pytest      # then commit pyproject.toml and uv.lock
```
