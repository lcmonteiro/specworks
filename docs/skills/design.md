# /specworks-design

:Phase: design
:Writes: `## Interfaces` in `design.md`; stubs in the code
:Next: `/specworks-test <ref>`
:Example: {doc}`../tutorial/design`

Agree on the API the change adds or extends, write it down, and create it as
stubs, so the test phase writes tests against the real names and signatures.
Use it when a change has been specified, or when you say "design the API",
"create the stubs" or "specworks design".

A **stub** has the real public signature (names, parameters, types, errors,
doc comments) and a body that only signals "not implemented"
(`raise NotImplementedError`, `throw new Error("not implemented")`,
`panic("not implemented")`, `todo!()`, ...). Error types and data shapes are
written in full.

## Steps

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 1 | Start the phase | `specworks start design --change <ref>` | exit 1 → show the failing checks of `gate specify`, suggest `/specworks-specify`, stop |
| 2 | Load the plan | `specworks task list --change <ref> --pending`; `specworks spec show <ref> --json` | the interface tasks; `codePath`, whose public API, naming and error style new interfaces follow |
| 3 | Propose the API, decide it with you | — | for each requirement: new and extended functions, classes, endpoints, data shapes, errors, the file each lives in; **BREAKING** marked |
| 4 | Record it | `specworks instructions design --change <ref>` (when no design.md yet) | one entry per interface under `## Interfaces`, its file in a code span; `None` when the API does not change |
| 5 | Create the stubs | — | — |
| 6 | Check and gate | `specworks run build`, `run typecheck` (when configured), `run test`; `specworks task done <N.M>`; `specworks gate design` | the existing suite must still pass; every failing blocking check to fix |
| 7 | Report and stop | — | table: interface, file, new or extended, requirements served; "run `/specworks-test <ref>`" |

## What the design gate checks

- `design.md` has an Interfaces section (`None` counts).
- Every file named in a code span there exists.
- The stubs build and typecheck (when those commands are configured).
- The existing tests still pass with the stubs. In a later build cycle, when
  the change already has `@ac` tests, a red suite is only a warning: changing
  an API turns its tests red on purpose, and the code phase makes them green.

All checks: {doc}`../reference/gates`.

## Guardrails

- No tests and no behaviour: stubs only signal "not implemented".
- No `@req` tags: they mark implemented code.
- Extending a function adds a stub for the new path only, never breaking
  behaviour existing tests rely on.
- The API serves the specs: if a requirement cannot be reached through a
  sensible API, or the API exposes something no requirement asks for, it stops
  and suggests `/specworks-specify`.
- Decided with you before code is written; design.md is the record.

## Source

````{dropdown} specworks-design/SKILL.md
:icon: code

```{literalinclude} ../../src/specworks/skills/specworks-design/SKILL.md
:language: markdown
```
````
