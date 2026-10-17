# /specworks-specify

:Phase: specify
:Writes: `proposal.md`, `specs/[<module>/]<capability>/spec.md`, `design.md` (when needed), `tasks.md`, `traceability.md`, all in the change folder
:Next: `/specworks-design <ref>`
:Example: {doc}`../tutorial/specify`

Decide **what** will change and **how it will be checked**, before any test or
code is written. Use it to plan a change, write requirements or acceptance
criteria, or when you say "specify", "spec this" or "write the proposal".

## Steps

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 1 | Pick the change, enter the phase | `specworks context --json`; `specworks new ... --json` when none fits; `specworks phase specify --change <ref>` | the change `ref` |
| 2 | Load what exists | `specworks status --change <ref> --json` | `artifacts[].status`: every `done` artifact is re-read from disk, `refinement.md` first (its recommendation and open questions drive the proposal) |
| 2b | Back from review? | `specworks cycle --change <ref> --json` | `open[]` with `"phase": "specify"`: the agreed proposals to carry out, and nothing more |
| 2c | Related capabilities | `specworks spec show <ref> --json`, `specworks spec list --json` | existing requirements; reuse an existing capability instead of a near-duplicate |
| 3 | Proposal | `specworks instructions proposal --change <ref> --json` | `template`, `instruction`, `outputPath`. The Capabilities section is the contract for step 4 |
| 4 | Delta specs | `specworks instructions specs --change <ref> --json`, then `specworks check --change <ref>` | per capability `deltaPath`, `prefix`, `nextId`; then every `error` of `check` to fix (`tasks.md is not written yet` is expected) |
| 5 | **Pause**: confirm | (a table: capability, requirement, criterion) | your corrections; `check` again; continue only on your confirmation |
| 6 | Design (when needed) | `specworks instructions design --change <ref> --json`; `specworks diagrams --change <ref>` | whether a design applies; D2 errors to fix |
| 7 | Tasks | `specworks instructions tasks --change <ref> --json` | the rules: grouped, `N.M`, IDs, verification, stubs → tests → code in each group |
| 8 | Validate, trace, gate | `specworks check`; `specworks trace --write`; `specworks gate specify` | errors to fix, warnings to fix or explain; the gate must pass |
| 9 | Report and stop | `specworks status --change <ref>` | summary; "run `/specworks-design <ref>`" |

## Delta spec rules

From the `specs` instruction ({doc}`../reference/artifacts`):

- ADDED requirements take new IDs from `nextId` upwards.
- MODIFIED copies the **whole** existing block (same ID) from the living spec,
  then edits it. A partial block loses detail at close.
- REMOVED gives the ID and title, plus **Reason** and **Migration**.
- Every requirement uses SHALL or MUST, one behaviour each, with at least one
  `#### Scenario: AC-<prefix>-NNN.<n>` with WHEN/THEN bullets.
- A new capability starts with `## Purpose` and has only ADDED requirements.
- A change with no behaviour change gets **no** delta spec:
  `specworks skip-specs --change <ref>`.

## Coming back from review

When review sends a finding back with `back to specify: ...`, this skill
carries out exactly that proposal, then adds under the finding in
`review.md`:

```markdown
  - done in specify: ADDED REQ-LINK-003 with AC-LINK-003.1
```

and leaves its box open. `specworks cycle` then starts the next build cycle at
design ({doc}`../reference/findings`).

## Guardrails

- Planning only: nothing outside the change folder. A request to implement
  does not carry over.
- IDs, prefixes and delta paths come from the CLI; an existing ID is never
  renumbered or reused.
- Never moves past step 5 without your confirmation.
- No invented requirements to satisfy validation.
- If the specs show the refinement was wrong, it says so and suggests
  `specworks phase refine` rather than silently changing scope.

## Source

````{dropdown} specworks-specify/SKILL.md
:icon: code

```{literalinclude} ../../src/specworks/skills/specworks-specify/SKILL.md
:language: markdown
```
````
