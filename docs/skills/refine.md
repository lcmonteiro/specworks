# /specworks-refine

:Phase: refine (first phase, optional for small changes)
:Writes: `refinement.md` only
:Next: `/specworks-specify <ref>`
:Example: {doc}`../tutorial/refine`

Build a shared understanding of the problem and its possible solutions before
committing to one. Use it when starting a new feature, fix or change that is
worth thinking through, or when you say "refine", "refinement" or
"specworks refine".

## Stance

- **Curious, not prescriptive**: ask the questions that unlock decisions.
- **Grounded**: read the real code, tests and capability docs before asking
  facts it could check itself.
- **One focused question at a time**, saying why it matters.
- **Honest about evidence**: separate what was observed from what is assumed.
- **No premature solution**: problem and constraints first, then options, then
  the recommendation.

## Steps

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 1 | Check the project | `specworks context --json` | `root` (`null` → stop, ask about `specworks init`); `context` (constraints); `capabilities[].docsPath` (living docs to read); `modules`, `missingModules`; `changes` (an existing change may already cover the request) |
| 2 | Select or create the change | `specworks new "<name>" [--module <m>] --json` | `ref`, announced as `Using change: <ref>` |
| 3 | Explore | (read code, tests, docs; talk) | the problem, scope, hard and soft constraints, 2-3 options, your preference |
| 4 | Write `refinement.md` | `specworks instructions refinement --change <ref> --json` | `template`, `instruction`, `outputPath`; `exists` → update, not overwrite. Asks "Ready to record the refinement?" first |
| 5 | Show the result and stop | `specworks status --change <ref>` | summary; "run `/specworks-specify <ref>`" |

The change name is kebab-case, derived from the request ("let users reset
passwords" → `add-password-reset`). The owning module is the one whose
behaviour changes; for several modules, the top level (or the lowest module
that contains all of them).

## Guardrails

- Only `refinement.md` in the change folder; never project code.
- Never runs `specworks init` unless you ask.
- Does not invent product intent, priorities or constraints.
- 1-2 pages; requirements, criteria, design and tasks belong to specify.
- Uses existing capability names (`module:capability`) when they fit.

## Source

````{dropdown} specworks-refine/SKILL.md
:icon: code

```{literalinclude} ../../src/specworks/skills/specworks-refine/SKILL.md
:language: markdown
```
````
