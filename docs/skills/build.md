# /specworks-build

:Phases: design → test → code → review, in cycles
:Writes: everything those four phases write
:Next: `/specworks-validate <ref>`
:Example: {doc}`../tutorial/review` and {doc}`../tutorial/build-cycle`

Take a specified change through design → test → code → review in one run,
then repeat the part of the cycle the review findings need, until the review
is clean or you stop. Each phase is done **exactly** as its own skill says
(same steps, gates and questions); this skill only chains them and decides
where a new cycle starts. Use it when you say "build the change", "run the
build cycle" or "specworks build".

```{mermaid}
flowchart TD
    A["gate specify<br/>status --json<br/>cycle --json"] -->|gate fails| X["stop: /specworks-specify"]
    A -->|startAt from open findings,<br/>or current phase,<br/>or design| B["Cycle n: run each phase's skill"]
    B --> D[design] --> T[test] --> C[code] --> R["review<br/>(records open findings,<br/>gate --allow-open)"]
    R --> Y["specworks cycle"]
    Y -->|no open findings| Z["trace --write<br/>suggest /specworks-validate"]
    Y -->|handOver: /specworks-specify| X
    Y -->|startAt = design / test / code| Q{"ask: start cycle n+1<br/>from startAt?"}
    Q -->|yes| B
    Q -->|no| S["stop; findings stay open<br/>in review.md"]
```

## Steps

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 1 | Where to start | `specworks gate specify`; `specworks status --json`; `specworks cycle --json` | gate fails → stop, `/specworks-specify`. Start at `startAt` when a review left open findings; else at the current phase if it is design, test, code or review; else at design |
| 2 | Run each phase | the phase skill's own steps (it moves the change with `specworks start`) | one-line result per phase instead of the phase's "Report and stop" |
| 3 | Review: propose, do not fix | `specworks gate review --allow-open` | findings that need work recorded open with `back to <phase>: ...` |
| 4 | Ask about a new cycle | `specworks cycle` | none open → done; `handOver: /specworks-specify` → stop; otherwise show the findings and ask "Start cycle n from X?" |
| 5 | Report and stop | `specworks trace --write` | per cycle: phases, API, tests, code, findings found/resolved/accepted |

## How the next cycle is chosen

| Open findings | Next cycle |
|---|---|
| `code-gap`, `tag`, `quality` | code → review |
| `test-gap` | test → code → review |
| `design-gap` | design → test → code → review |
| `spec-gap` | stop; `/specworks-specify`, then `/specworks-build` resumes at design |

The earliest phase any finding needs wins. A `back to <phase>:` in a
Decision overrides the type; a `done in <phase>:` line moves the finding to the
phase after that one. From cycle 2 on, each phase works only on its findings
(and what later phases need to follow them).

After the third cycle the skill says how many cycles ran and what keeps
coming back: repeated findings usually mean the spec or design needs a
decision, not another cycle.

## Guardrails

- Every phase follows its own skill; no gate or decision is skipped.
- A new cycle starts only after you say yes, and only from the phase the
  findings need.
- Spec problems are never fixed inside the build.
- No weakened tests, skipped gates or findings marked resolved to finish a cycle.

## Source

````{dropdown} specworks-build/SKILL.md
:icon: code

```{literalinclude} ../../src/specworks/skills/specworks-build/SKILL.md
:language: markdown
```
````
