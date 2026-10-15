---
name: specworks-specify
description: Specify phase of spec-driven development - turn a request (or a refinement) into a proposal, delta specs with requirement IDs and acceptance criteria, a design and a task list, validated and traced. Use in a specworks project when the user wants to plan a change before building it, write requirements or acceptance criteria, or says "specify", "spec this", "write the proposal" or "specworks specify".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx:*), Read, Grep, Glob, Write, Edit
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

---

## Steps

1. **Check the project and pick the change**

   ```bash
   specworks context --json
   ```

   - `"root": null`: the project is not set up. Stop and ask whether to run
     `specworks init`. Do not create files by hand.
   - Apply `context` as constraints (it is already merged top level → module);
     never copy it into an artifact.
   - If the user named a change, or one in `changes` matches the request, use
     it. Otherwise create one as `/specworks-refine` does (kebab-case name,
     owning module, `specworks new "<name>" [--module <m>] --json`); refinement
     is optional for small changes.
   - Announce `Using change: <ref>` and move it to this phase:
     ```bash
     specworks phase "<ref>" specify
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
  change sets `skip_specs: true` in `.change.yaml` and has no delta specs.
- Do not move past step 5 without the user's confirmation.
- If the specs reveal that the refinement was wrong, say so and suggest going
  back (`specworks phase "<ref>" refine`) rather than silently changing scope.
