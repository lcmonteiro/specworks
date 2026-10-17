# Phases and gates

A change is always in exactly one phase, stored in its `.change.yaml`:

```text
refine → specify → design → test → code → review → validate → close → done
```

| Phase | Skill | Output |
|---|---|---|
| refine | `/specworks-refine` | `refinement.md`: problem, context, constraints, options, recommendation |
| specify | `/specworks-specify` | `proposal.md`, delta specs (requirements + acceptance criteria), `design.md`, `tasks.md`, `traceability.md` |
| design | `/specworks-design` | the API decided with you, recorded under Interfaces in `design.md`, created as stubs that build |
| test | `/specworks-test` | failing tests tagged `@ac` for every acceptance criterion |
| code | `/specworks-code` | real code replacing the stubs, `@req` tags, tests green |
| review | `/specworks-review` | drift between code, spec and design found and decided; `review.md` |
| validate | `/specworks-validate` | read-only PASS/FAIL report |
| close | `/specworks-close` | deltas merged into the living `spec.md`, living docs updated, change archived (`done`) |

## Moving a change

| Command | Checks first? | Used by |
|---|---|---|
| `specworks start <phase>` | **yes**: runs the gates the move depends on; moves only if they all pass (exit 1, phase unchanged, otherwise) | every phase skill from design on, as its first step |
| `specworks phase <phase>` | no | `/specworks-specify` (enter specify), `/specworks-review` (send a change back), you when you know what you are doing |
| `specworks close` | yes: the full validate | `/specworks-close`; the only way to reach `done` |

Which gates `start` runs:

- **Moving forward**, every phase left behind must pass its gate:
  `start test` from specify runs `gate specify` *and* `gate design`.
- **Going back or re-entering**, only the gate of the phase just before the
  target runs: `start test` from review runs only `gate design`.

The full table is in {doc}`../reference/start-rules`.

```{mermaid}
stateDiagram-v2
    [*] --> refine: specworks new
    refine --> specify: phase specify
    specify --> design: start design (gate specify)
    design --> test: start test (gate design)
    test --> code: start code (gate test)
    code --> review: start review (gate code)
    review --> validate: start validate (gate review)
    validate --> close: start close (gate validate)
    close --> done: specworks close (merge + archive)
    done --> [*]

    test --> design: a test needs an API that was not agreed
    design --> specify: the spec is wrong
    review --> code: back to code
    review --> test: back to test
    review --> design: back to design
    review --> specify: back to specify
    validate --> code: FAIL → the phase each check names
```

## What each gate requires

| Gate | Passes when |
|---|---|
| `specify` | specs and tasks are valid (`specworks check`), `tasks.md` is written, every criterion is covered by a task |
| `design` | `design.md` has `## Interfaces`, every file named there exists, build and typecheck (when configured) and the existing tests pass |
| `test` | every criterion has an `@ac` test, no tag points to an unknown ID |
| `code` | every task is ticked, every requirement has `@req` code, every criterion is still tested, removed requirements are gone, the suite is green |
| `review` | `review.md` is written with no open finding (or `--allow-open` in a build), every untagged changed file is accounted for, tags are complete, the suite is green |
| `validate` | the full validate report has no critical failure |

Every check of every gate: {doc}`../reference/gates`.

## Phases are not strictly linear

The dashed arrows in the workflow diagram are the ways back:

- `test` goes back to `design` when a test needs an API that was not agreed.
- `design`, `test` and `code` go back to `specify` when the spec turns out wrong.
- `review` proposes, for each drift, a change to the code, the spec or the
  design: small, local ones are applied there with you, larger ones go back to
  `code`, `specify` or `design`.
- A failing `validate` names the phase that fixes each problem.
