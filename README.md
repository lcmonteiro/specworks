# specworks

Spec-driven development for AI coding agents, modelled on
[OpenSpec](https://github.com/Fission-AI/OpenSpec) and rewritten in Python (managed with `uv`).

```
refine -> propose -> tests -> code -> review -> verify -> done
```

| Phase   | Skill         | Output |
|---------|---------------|--------|
| refine  | `/sw-refine`  | `refinement.md`: problem, context, constraints, options, recommendation |
| propose | `/sw-propose` | proposal, requirements + acceptance criteria, design, tasks, traceability *(planned)* |
| tests   | `/sw-tests`   | failing tests per acceptance criterion + API stubs *(planned)* |
| code    | `/sw-code`    | implementation driven by tasks and specs *(planned)* |
| review  | `/sw-review`  | code <-> spec drift fixed *(planned)* |
| verify  | `/sw-verify`  | completeness / correctness / traceability report *(planned)* |
| done    | `/sw-done`    | living docs merged into `<capability-path>/docs/` *(planned)* |

## Layout

```
specworks.yaml                     # dir, context, capabilities -> code paths
<dir>/changes/<name>/              # in-flight change artifacts
<dir>/changes/archive/             # finished changes
<capability-path>/<docs_dir>/      # living docs, next to the code
```

`<dir>` defaults to `specworks`. Pick another name with `specworks init --dir spec`
(or `docs`, `context`, `docs/spec`, ...), or change `dir:` in `specworks.yaml` later.
`<docs_dir>` defaults to `docs`.

## Modules (sub-projects)

Like git submodules, a project can link other folders that have their own
`specworks.yaml`. Each module is a complete project (own `dir`, context,
capabilities and changes), and the parent lists it explicitly:

```yaml
# specworks.yaml (top level)
modules:
  billing: services/billing
```

```
repo/
  specworks.yaml          # top level: lists billing
  spec/changes/           # cross-module changes
  services/billing/
    specworks.yaml        # module: lists tax
    spec/changes/         # billing's own changes
    src/invoices/docs/    # living docs of billing:invoices
    tax/specworks.yaml    # nested module billing/tax
```

- `specworks module add <path>` (or `specworks init <path>` under a project) creates and links a module.
- Every module uses the **same folder name** as the top level (`dir`, set once by `specworks init --dir ...`).
  A module may leave `dir` out; setting a different one is an error.
- Commands act on the **nearest** module; `--all` shows the whole workspace.
- Context is **inherited**: top-level context first, then each module down to the current one.
- Capabilities and changes of other modules are named `module:name` (`billing:invoices`, `billing/tax:add-vat`).
- A listed module whose folder has no config (e.g. a submodule not checked out) shows up under `missingModules`.

## Install

```bash
uv tool install git+https://github.com/lcmonteiro/specworks
cd your-project && specworks init     # writes specworks.yaml and .claude/skills/sw-*
```

## Development

```bash
uv sync
uv run pytest
uv run specworks --help
```
