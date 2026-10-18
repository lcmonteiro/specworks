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

The documentation is this wiki: edit a page in the wiki's web editor, or clone
`https://github.com/lcmonteiro/specworks.wiki.git` and push. The file name is the
page name, and links between pages use it: `[Phases and gates](Concepts-Phases)`.
`_Sidebar.md` is the navigation, `images/` holds the images.

Some pages show a file of the main repository in full: each skill page its
`SKILL.md`, the reference `schema.yaml` and the templates, the tutorial the
files of the example project in
[`examples/shortlink/`](https://github.com/lcmonteiro/specworks/tree/main/examples/shortlink).
Each copy follows a marker naming its source:

    <!-- include: src/specworks/schema.yaml -->
    ```yaml
    ...
    ```

Nothing updates these copies: when you change a skill, a template or the
example project, update the page that shows it.

Command output in the tutorial and the CLI reference was captured by running
specworks on the example project. When a command's output changes, run it
again in a copy of `examples/shortlink/` and update the page.

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
