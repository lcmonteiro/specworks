# CLI reference

Every `specworks` command, with its options, exit codes, and real output from
the {doc}`tutorial <../tutorial/index>` project. `specworks <command> --help`
prints the same options.

## Conventions

`--change <ref>` / `-c <ref>`
: The change to act on: its name (`add-short-links`) in the current module, or
  `module:name` (`analytics:track-clicks`) for another module. Archived changes
  are accepted where it makes sense (`status`), by name or by `<date>-<name>`.

`--json`
: Machine-readable output. Every command has it; it is what the skills read.
  Change-related commands start their JSON with the change's `name`, `ref`,
  `module`, `path`, `phase`, `created` and `skipSpecs`.

`--base <branch>`
: The branch `review`, `gate review`, `start` and `validate` compare the change
  with. Default: origin's default branch (`origin/main`, `main`,
  `origin/master`, `master`).

`--no-run`
: Gates and validate do not run the project's commands; those checks become
  warnings (`not run (--no-run); run specworks run <key>`).

`--fresh`
: Run the project's commands for real even when a result from the same code
  exists ({doc}`../reference/run-cache`).

Exit codes
: `0` success; `1` a blocking check failed, a gate did not pass, or an error
  (printed as `error: <message>` on stderr). `specworks run` passes the
  project command's own exit code through.

The working directory decides the **current module**: commands act on the
nearest config in this folder or its parents.

## Commands by area

| Area | Commands |
|---|---|
| {doc}`project` | `version`, `init`, `skills`, `context`, `module add`, `module list` |
| {doc}`changes` | `new`, `list`, `status`, `phase`, `start`, `skip-specs`, `abandon` |
| {doc}`specs` | `spec list`, `spec show`, `capability add`, `instructions`, `check`, `trace`, `task list/done/undo`, `diagrams` |
| {doc}`workflow` | `gate`, `run`, `review`, `cycle`, `validate`, `close` |

```{toctree}
:maxdepth: 2

project
changes
specs
workflow
```
