---
name: specworks-specify
description: Specify phase of spec-driven development - turn a request (or a refinement) into a proposal, delta specs with requirement IDs and acceptance criteria, a design and a task list, validated and traced. Use in a specworks project when the user wants to plan a change before building it, write requirements or acceptance criteria, or says "specify", "spec this", "write the proposal" or "specworks specify".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Bash(git add:*), Bash(git commit:*), Read, Grep, Glob, Write, Edit
---

Specify phase: decide WHAT will change and HOW it will be checked, before any
test or code is written. It produces, inside the change folder:

- `proposal.md`: why, what changes, which capabilities
- `specs/[<module>/]<capability>/spec.md`: delta specs, requirements `REQ-…` with acceptance criteria `AC-…`
- `design.md`: how, when the change needs one
- `tasks.md`: ordered checklist, every task naming the IDs it serves
- `traceability.md`: generated matrix REQ → AC → tasks (→ tests → code later)

It is the second phase of `refine → specify → design → implement (test | code) → review → validate → close`.

**Phase boundary**: planning only. Do not write tests or code and do not edit
files outside the change folder, even if the request says "build" or "fix".
When the artifacts are done, stop and offer `/specworks-build` (or
`/specworks-design` for one phase at a time).

<!-- specworks:include running-cli -->

<!-- specworks:include asking-the-user -->

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
   it), starting with `refinement.md` if present: its outcomes, recommended
   option and open questions drive the proposal. Every outcome is covered by
   a requirement or listed under Out of Scope. If a planning artifact already
   exists, continue from it instead of overwriting it.

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
   compatibility or acceptance criteria, each question with its options and
   the one you recommend. Decide small details yourself and
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

   plus any assumption you made. Say that design and tasks are built on
   them, and ask: "Are these the right requirements and acceptance
   criteria? (yes/no)". **Stop and wait.**
   Apply the user's corrections, re-run `specworks check`, and continue only
   when they confirm. Agreeing to earlier answers is not confirmation of this
   list.

6. **Write `design.md` (only when needed)**

   ```bash
   specworks instructions design --change "<ref>" --json
   ```

   The `instruction` says when a design is worth writing. If none applies,
   skip it and tell the user why in one line. When written, name the
   interfaces (APIs, data shapes, CLI surfaces) the test half will target,
   and resolve open questions that would change the tasks with the user now.

   Diagrams follow the rule in `instruction`: a change that adds, removes or
   moves components, or changes the dependencies between them, gets one
   block diagram per capability whose structure changes, written as
   `diagrams/<capability>-blocks.d2` (close looks for that name); otherwise
   `## Diagrams` says "No structural change". Write any other diagram as
   `diagrams/<name>.d2`. Put them in the change folder following the D2 rules
   in `instruction` (no colours or styles; the theme handles the look), then
   render and embed them:
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
   in every group; every acceptance criterion is covered. Follow the
   instruction's rules, above all how a `[code]` task is verified, and fix
   every `check` warning about the tasks before the gate.

8. **Validate, trace and gate**

   ```bash
   specworks check --change "<ref>"
   specworks trace --change "<ref>" --write
   specworks gate specify --change "<ref>"
   ```

   Fix every validation error (warnings: fix or explain). `trace` writes
   `traceability.md`; at this phase the test and code columns are empty.
   `gate specify` must pass: it is what `/specworks-design` checks first.

<!-- specworks:include committing -->

9. **Show the result and stop**

   ```bash
   specworks status --change "<ref>"
   ```

   Summarize: change and location; each artifact in one line (and design
   skipped, if so); the number of requirements and acceptance criteria per
   capability; assumptions made; review findings marked `done in specify`.
   Say "The plan is ready for review." and end with:
   ```
   1. /specworks-build <ref> (recommended): design, test, code and review in one run
   2. /specworks-design <ref>: one phase at a time, starting with the API as stubs
   3. Stop here
   ```

---

## Guardrails

- Planning only: write inside the change folder, nothing else. A request to
  implement does not carry over; wait for `/specworks-design`, then
  `/specworks-test` and `/specworks-code` (the two halves of implement).
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
