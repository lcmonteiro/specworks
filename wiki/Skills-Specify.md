# /specworks-specify

:Phase: specify
:Writes: `proposal.md`, `specs/[<module>/]<capability>/spec.md`, `design.md` (when needed), `tasks.md`, `traceability.md`, all in the change folder
:Next: `/specworks-design <ref>`
:Example: [2. specify](Tutorial-Specify)

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

From the `specs` instruction ([Artifacts: instructions and templates](Reference-Artifacts)):

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
design ([Review findings and build cycles](Reference-Findings)).

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

<details>
<summary>specworks-specify/SKILL.md</summary>

<!-- include: src/specworks/skills/specworks-specify/SKILL.md -->
````markdown
---
name: specworks-specify
description: Specify phase of spec-driven development - turn a request (or a refinement) into a proposal, delta specs with requirement IDs and acceptance criteria, a design and a task list, validated and traced. Use in a specworks project when the user wants to plan a change before building it, write requirements or acceptance criteria, or says "specify", "spec this", "write the proposal" or "specworks specify".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Read, Grep, Glob, Write, Edit
---

Specify phase: decide WHAT will change and HOW it will be checked, before any
test or code is written. It produces, inside the change folder:

- `proposal.md`: why, what changes, which capabilities
- `specs/[<module>/]<capability>/spec.md`: delta specs, requirements `REQ-…` with acceptance criteria `AC-…`
- `design.md`: how, when the change needs one
- `tasks.md`: ordered checklist, every task naming the IDs it serves
- `traceability.md`: generated matrix REQ → AC → tasks (→ tests → code later)

It is the second phase of `refine → specify → design → test → code → review → validate → close`.

**Phase boundary**: planning only. Do not write tests or code and do not edit
files outside the change folder, even if the request says "build" or "fix".
When the artifacts are done, stop and suggest `/specworks-design`.

<!-- specworks:include running-cli -->

<!-- specworks:include picking-the-change -->

---

## Steps

1. **Check the project and pick the change**

   - Pick the change (above). When none fits the request, create one as
     `/specworks-refine` does (kebab-case name, owning module,
     `specworks new "<name>" [--module <m>] --json`); refinement is optional
     for small changes.
   - Move it to this phase:
     ```bash
     specworks phase specify --change "<ref>"
     ```

2. **Load what exists**

   ```bash
   specworks status --change "<ref>" --json
   ```

   Re-read from disk every artifact that is `done` (the user may have edited
   it), starting with `refinement.md` if present: its recommended option and
   open questions drive the proposal. If a planning artifact already exists,
   continue from it instead of overwriting it.

   **Back from review**: if the change has a `review.md`, list its open
   findings with `specworks cycle --change "<ref>" --json`. Those with
   `"phase": "specify"` are why the change is back here: carry out the agreed
   proposal in each one's Decision (`back to specify: ...`) in the delta
   specs, tasks and design.md, and nothing more. Once `gate specify` passes
   (step 8), add a line under each of those findings in review.md:
   `  - done in specify: <what changed, with the IDs added or modified>`.
   Leave its box open (`- [ ]`): review ticks it once tests and code follow,
   and `specworks cycle` now starts the next build cycle at design instead of
   handing the change back to specify.

   Inspect the code, tests and docs the change touches (read-only), and the
   living specs of related capabilities:
   ```bash
   specworks spec show "<ref>" --json      # one capability: requirements, prefix, nextId, deltaPath
   specworks spec list --json              # every capability of the workspace
   ```

   Ask the user about anything that would change scope, observable behaviour,
   compatibility or acceptance criteria. Decide small details yourself and
   record the assumption in the proposal.

3. **Write `proposal.md`**

   ```bash
   specworks instructions proposal --change "<ref>" --json
   ```

   Use `template` and `instruction`; write to `outputPath`. The Capabilities
   section is the contract for the next step: every capability listed there
   gets a delta spec. For a new capability, say which module owns it and its
   code path.

4. **Write the delta specs**: requirements and acceptance criteria

   ```bash
   specworks instructions specs --change "<ref>" --json
   ```

   For each capability in the proposal, one at a time:
   - Get its `deltaPath`, `prefix` and `nextId` from `capabilities` in that
     response, or `specworks spec show "<ref>" --json` (also works for a new
     capability). Never invent paths or IDs.
   - Write `<changeDir>/<deltaPath>` following `instruction`: ADDED with new
     IDs from `nextId` upwards, MODIFIED with the whole existing block, REMOVED
     with Reason and Migration. Every requirement uses SHALL/MUST and has
     acceptance criteria `#### Scenario: AC-<prefix>-NNN.<n> <title>` with
     WHEN/THEN.

   Then validate and fix every error before going on:
   ```bash
   specworks check --change "<ref>"
   ```
   (`tasks.md is not written yet` is expected at this point.)

5. **Pause: confirm requirements and acceptance criteria with the user**

   Show a compact table, one line per acceptance criterion:

   ```
   Capability  Requirement                       Acceptance criterion
   user-auth   REQ-AUTH-003 Password reset (ADDED)  AC-AUTH-003.1 Request reset
                                                    AC-AUTH-003.2 Expired link
   user-auth   REQ-AUTH-002 Lockout (MODIFIED)      AC-AUTH-002.1 Third failure
   ```

   plus any assumption you made. Ask: "Are these the right requirements and
   acceptance criteria? Design and tasks are built on them." **Stop and wait.**
   Apply the user's corrections, re-run `specworks check`, and continue only
   when they confirm. Agreeing to earlier answers is not confirmation of this
   list.

6. **Write `design.md` (only when needed)**

   ```bash
   specworks instructions design --change "<ref>" --json
   ```

   The `instruction` says when a design is worth writing. If none applies,
   skip it and tell the user why in one line. When written, name the
   interfaces (APIs, data shapes, CLI surfaces) the test phase will target,
   and resolve open questions that would change the tasks with the user now.

   Diagrams, when they help: write `diagrams/<name>.d2` in the change folder
   following the D2 rules in `instruction` (no colours or styles; the theme
   handles the look), then render and embed them:
   ```bash
   specworks diagrams --change "<ref>"
   ```
   Fix any D2 error it reports (often an unquoted label with `{` or `:`).
   If it says d2 cannot run (a broken pyd2 install), keep the `.d2` files,
   pass the error to the user, and continue; `validate` will remind you later.

7. **Write `tasks.md`**

   ```bash
   specworks instructions tasks --change "<ref>" --json
   ```

   Ordered `- [ ] N.M` tasks; each names its REQ/AC IDs and how to verify it;
   failing tests (tagged `@ac`) come before the implementation (tagged `@req`)
   in every group; every acceptance criterion is covered.

8. **Validate, trace and gate**

   ```bash
   specworks check --change "<ref>"
   specworks trace --change "<ref>" --write
   specworks gate specify --change "<ref>"
   ```

   Fix every validation error (warnings: fix or explain). `trace` writes
   `traceability.md`; at this phase the test and code columns are empty.
   `gate specify` must pass: it is what `/specworks-design` checks first.

9. **Show the result and stop**

   ```bash
   specworks status --change "<ref>"
   ```

   Summarize: change and location; each artifact in one line (and design
   skipped, if so); the number of requirements and acceptance criteria per
   capability; assumptions made; review findings marked `done in specify`.
   End with: "The plan is ready for review.
   When you are ready, run `/specworks-design <ref>` to decide the API and
   create it as stubs."

---

## Guardrails

- Planning only: write inside the change folder, nothing else. A request to
  implement does not carry over; wait for `/specworks-design`,
  `/specworks-test` and `/specworks-code`.
- IDs, prefixes and delta paths come from the CLI (`nextId`, `prefix`,
  `deltaPath`). Never renumber or reuse an existing ID; a removed requirement's
  ID is retired.
- Always re-read artifacts from disk before building on them.
- Do not invent requirements to satisfy validation. A change with no behaviour
  change has no delta specs and is marked with
  `specworks skip-specs --change "<ref>"`.
- Do not move past step 5 without the user's confirmation.
- If the specs reveal that the refinement was wrong, say so and suggest going
  back (`specworks phase refine --change "<ref>"`) rather than silently changing scope.
````

</details>
