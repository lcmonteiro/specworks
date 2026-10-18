# Python API

The `specworks` package, module by module. The CLI is a thin layer
(`specworks.cli`) over these modules; the code layout in
[Development](Development) explains how they fit. Every module and public
function has a docstring: read it in the source, or with
`uv run python -m pydoc specworks.core.config`.

| Package | What it holds |
|---|---|
| [`specworks.core`](https://github.com/lcmonteiro/specworks/tree/main/src/specworks/core) | `config.py` (find and read `<dir>.yml`), `config_file.py` (write it), `workspace.py` (modules), `changes.py` (changes and phases), `runner.py` (project commands and the run cache), `git.py`, `files.py`, `validators.py`, `errors.py` |
| [`specworks.specs`](https://github.com/lcmonteiro/specworks/tree/main/src/specworks/specs) | `specfile.py` (parse specs), `capabilities.py`, `check.py` (`specworks check`), `tasks.py`, `trace.py` (tags, matrix, and `Analysis`), `merge.py` (close) |
| [`specworks.workflow`](https://github.com/lcmonteiro/specworks/tree/main/src/specworks/workflow) | `artifacts.py` (artifacts and instructions), `checks.py` (every check, each defined once), `gate.py`, `review.py` (drift and `review.md`), `cycle.py`, `validate.py` |
| [`specworks.tools`](https://github.com/lcmonteiro/specworks/tree/main/src/specworks/tools) | `diagrams.py` (D2 via pyd2), `skills.py` (install the skills) |
| [`specworks.cli`](https://github.com/lcmonteiro/specworks/tree/main/src/specworks/cli) | the Typer app and one module per area of commands |
