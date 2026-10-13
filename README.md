# specworks

Spec-driven development for AI coding agents, inspired by
[OpenSpec](https://github.com/Fission-AI/OpenSpec) and written in Python (managed with `uv`).

```
refine -> propose -> test -> implement -> review -> verify -> close
```

| Phase     | Skill                  | Output |
|-----------|------------------------|--------|
| refine    | `/specworks-refine`    | `refinement.md`: problem, context, constraints, options, recommendation |
| propose   | `/specworks-propose`   | proposal, requirements + acceptance criteria, design, tasks, traceability *(planned)* |
| test      | `/specworks-test`      | failing tests per acceptance criterion + API stubs *(planned)* |
| implement | `/specworks-implement` | implementation driven by tasks and specs *(planned)* |
| review    | `/specworks-review`    | fixes code <-> spec drift; **may edit** code and spec deltas *(planned)* |
| verify    | `/specworks-verify`    | pass/fail report (completeness, correctness, traceability); **read-only** gate before close *(planned)* |
| close     | `/specworks-close`     | living docs merged into `<capability-path>/docs/`, change archived (phase `done`) *(planned)* |

The flow is not strictly linear: `review` can send a change back to `propose`
(missing requirement) and a failing `verify` sends it back to `implement`.
`specworks phase <change> <phase>` moves a change to any phase.

## Layout

```
<dir>.yml                          # config: context, capabilities -> code paths, modules
<dir>/changes/<name>/              # in-flight change artifacts
<dir>/changes/archive/             # finished changes
<capability-path>/<docs_dir>/      # living docs, next to the code
```

The config file is named after the workflow folder: `specworks init --dir spec`
creates `spec.yml` and `spec/` (or `docs.yml` + `docs/`, `context.yml` + `context/`, ...).
`<dir>` defaults to `specworks`. To rename later, rename both the file and the folder.
The file starts with `specworks: 1`, which marks it as a specworks config (so an
unrelated `docs.yml` is never mistaken for one).
`<docs_dir>` defaults to `docs`.

## Modules (sub-projects)

Like git submodules, a project can link other folders that have their own
config. Each module is a complete project (own context, capabilities and
changes), and the parent lists it explicitly:

```yaml
# spec.yml (top level)
specworks: 1
modules:
  billing: services/billing
```

```
repo/
  spec.yml                # top level: lists billing
  spec/changes/           # cross-module changes
  services/billing/
    spec.yml              # module: lists tax
    spec/changes/         # billing's own changes
    src/invoices/docs/    # living docs of billing:invoices
    tax/spec.yml          # nested module billing/tax
```

- `specworks module add <path>` (or `specworks init <path>` under a project) creates and links a module.
- Every module uses the **same config and folder name** as the top level (set once by
  `specworks init --dir ...`): `spec.yml` + `spec/` everywhere. A module with another
  name (e.g. `docs.yml`) is an error that says what to rename.
- Commands act on the **nearest** module; `--all` shows the whole workspace.
- Context is **inherited**: top-level context first, then each module down to the current one.
- Capabilities and changes of other modules are named `module:name` (`billing:invoices`, `billing/tax:add-vat`).
- A listed module whose folder has no config (e.g. a submodule not checked out) shows up under `missingModules`.

## Install

```bash
uv tool install git+https://github.com/lcmonteiro/specworks
cd your-project && specworks init --dir spec   # writes spec.yml, spec/ and .claude/skills/specworks-*
```

## Development

```bash
uv sync
uv run pytest
uv run specworks --help
```
