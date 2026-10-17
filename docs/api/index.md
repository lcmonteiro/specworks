# Python API

The `specworks` package, module by module, generated from its docstrings. The
CLI is a thin layer (`specworks.cli`) over these modules; the
[README's code layout](https://github.com/lcmonteiro/specworks#development)
explains how they fit.

| Package | What it holds |
|---|---|
| {doc}`core` | `config.py` (find and read `<dir>.yml`), `config_file.py` (write it), `workspace.py` (modules), `changes.py` (changes and phases), `runner.py` (project commands and the run cache), `git.py`, `files.py`, `validators.py`, `errors.py` |
| {doc}`specs` | `specfile.py` (parse specs), `capabilities.py`, `check.py` (`specworks check`), `tasks.py`, `trace.py` (tags, matrix, and `Analysis`), `merge.py` (close) |
| {doc}`workflow` | `artifacts.py` (artifacts and instructions), `checks.py` (every check, each defined once), `gate.py`, `review.py` (drift and `review.md`), `cycle.py`, `validate.py` |
| {doc}`tools` | `diagrams.py` (D2 via pyd2), `skills.py` (install the skills) |
| {doc}`cli` | the Typer app and one module per area of commands |

```{toctree}
:maxdepth: 2

core
specs
workflow
tools
cli
```
