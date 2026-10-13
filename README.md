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
specworks.yaml                     # context, capabilities -> code paths
specworks/changes/<name>/          # in-flight change artifacts
specworks/changes/archive/         # finished changes
<capability-path>/docs/            # living docs, next to the code
```

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
