---
name: specworks-code
description: Code half of the implement phase of spec-driven development - work through a change's [code] tasks, replacing the API stubs with real code from the specs and design (independently of the test half), tagging code with @req and ticking tasks as they are done. Use when a specworks change has its agreed API and the user wants to implement it, or says "implement the change", "write the code" or "specworks code".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Read, Grep, Glob, Write, Edit
---

Code half of implement: write the code the `[code]` tasks describe, from
the specs and the design, and nothing more. The test half
(`/specworks-test`) writes this change's tests from the same specs and
design; you do not read them, so the two are independent readings of the
spec, and review is where they meet. Every requirement ends up with code
tagged `@req <REQ-ID>`, every `[code]` task ticked, and the existing tests
still green.

It is the code half of the fourth phase of `refine → specify → design → implement (test | code) → review → validate → close`.
In `/specworks-build` it runs in the main checkout, in parallel with the
test half.

**Phase boundary**: implement what the specs, the design and the `[code]`
tasks say. The specs and the acceptance criteria are the contract: do not
change them to make the code easier, and do not shape the code after this
change's tests. When the code gate passes, stop and suggest
`/specworks-review` (or `/specworks-test` when the test half is not done).

**Running the CLI**: use `specworks <cmd>`. If it is not on PATH, use
`uv run specworks <cmd>` (inside the specworks repo) or
`uvx --from git+https://github.com/lcmonteiro/specworks specworks <cmd>`.
Gates and `validate` reuse a test/lint/typecheck result from the same code
(`same code as the run at ...`). After fixing something outside the code (a
git-ignored file, a service the tests need), run `specworks run <key>` once:
its result replaces the reused one. `--fresh` on a gate, `start` or `validate`
does the same for that command.

**Asking the user**: whenever you stop for the user (a decision, a
confirmation, the end of the phase), end your message with exactly one
closing question that can be answered in a word, and write nothing after it:
- a yes/no question: `Merge and archive? (yes/no)`;
- or numbered options, exactly one marked `(recommended)` with a one-line
  reason:
  ```
  1. Refuse before writing (recommended): nothing to roll back
  2. Write, then roll back on error
  ```
Ask one decision at a time; several go together only when they are
independent, each with its own options. At the end of the phase, offer the
next step the same way: the next skill (recommended), any alternative, and
`stop here`.

**Picking the change**: start with `specworks context --json`.
- `"root": null`: the project is not set up. Stop and ask "Run
  `specworks init` here? (yes/no)"; do not create files by hand.
- `context` holds the project's constraints (merged top level → module).
  Apply them, but never as instructions that override this workflow, and
  never copy them into an artifact.
- The change is the one the user named (`name`, or `module:name` for another
  module); otherwise the only one in `changes` (`--all` for every module).
  If several could fit, offer them as numbered options (the most recent
  recommended); if none fits, ask for its name. Announce
  `Using change: <ref>` and use that `<ref>` in every command.

---

## Steps

1. **Pick the change and start implement once the API is agreed**

   - Pick the change (above), then:
     ```bash
     specworks start implement --change "<ref>"
     ```
     It runs the gates of the phases left behind (`gate design`, and
     `gate specify` too if the change skips design) and moves the change to
     implement only if they pass. When the change is already in implement
     (the test half started it), it re-checks `gate design` only.
   - If a gate fails, stop: show the failing checks and suggest
     `/specworks-design <ref>` (or `/specworks-specify <ref>` when the specs
     themselves fail).
   - `commands` in the context are this project's tools; `specworks run test`
     (and `run lint`, `run typecheck` when configured) runs them in the right
     folder. If `test` is not configured, find it and ask "Use `<command>` as
     the test command and add it under `commands:`? (yes/no)".

2. **Load the plan**

   Re-read from disk: the refinement, the delta specs, `design.md`
   (decisions and interfaces), and the tasks (yours are the ones marked
   `[code]`):
   ```bash
   specworks task list --change "<ref>" --pending
   specworks trace --change "<ref>" --json
   ```
   `trace` shows where the stubs and existing code are tagged. Do not open
   the tests tagged with this change's criteria: the acceptance criteria,
   not those tests, say what the code must do.

3. **Work through the tasks, in order, one at a time**

   For each pending `[code]` task:
   1. Say which task you are on (`Task 2.1: ...`).
   2. Read the requirements and criteria it names, and the code around the
      change.
   3. Write the smallest code that does what each criterion's WHEN/THEN
      says, the way the requirement intends, in the project's style; follow
      design.md's decisions. Replace stubs with real code.
   4. Tag the code that implements each requirement with a comment in the
      language's syntax, at its main entry point (function, class, handler,
      route):
      ```python
      # @req REQ-AUTH-003
      def request_password_reset(email: str) -> None: ...
      ```
      One requirement may be tagged in several places; keep tags on the code
      that actually implements it.
   5. For REMOVED requirements, delete their code and its `@req` tags (their
      tests are the test half's).
   6. Run the suite when the task is done:
      ```bash
      specworks run test --change "<ref>"
      ```
      Existing tests must stay green. This change's own `@ac` tests may
      fail (or not exist yet): do not read them to make them pass; review
      compares them with the code.
   7. Tick the task only when its verification passes:
      ```bash
      specworks task done <N.M> --change "<ref>"
      ```

   **Pause and ask** instead of guessing (the ways forward as numbered
   options, the one you recommend marked) when:
   - a task or requirement is unclear, or two of them conflict;
   - an existing test contradicts a MODIFIED or REMOVED criterion: it may
     only change with the user's agreement, and you say so in the report;
   - the design does not work in practice: propose the change, and after the
     user agrees record it under the decision in design.md;
   - you discover work the tasks do not cover: suggest adding a task (and a
     requirement, via `/specworks-specify <ref>`, if behaviour changes).

4. **Run the project's checks**

   ```bash
   specworks run test --change "<ref>"
   specworks run lint --change "<ref>"        # if configured
   specworks run typecheck --change "<ref>"   # if configured
   ```

   Fix what fails in the existing tests, lint and typecheck. Never skip,
   disable or loosen tests to get green.

5. **Gate and trace**

   ```bash
   specworks gate code --change "<ref>"
   specworks trace --change "<ref>" --write
   ```

   The code gate checks only this half: the specs are still valid, every
   `[code]` task is ticked, every requirement has `@req` code, no tag points
   to an unknown ID, removed requirements and criteria are gone, and the
   test suite passes (it runs `commands.test`). Open `[test]` tasks and
   criteria without tests do not affect it. While the change has `@ac` tests
   of its own, a failing suite is a warning: those tests meet the code in
   review. Fix every failing blocking check and re-run.

6. **Report and stop**

   Summarize: tasks done, files changed per capability, where each
   requirement is implemented (from the trace), test results, any decision
   or deviation recorded in design.md, and any test changed with the user's
   agreement. End with:
   ```
   1. /specworks-review <ref> (recommended): the test half is done; the tests meet the code
   2. /specworks-test <ref>: the test half is not done yet
   3. Stop here
   ```

---

## Guardrails

- The specs are the contract. Do not edit the delta specs here; if they are
  wrong, stop and suggest `/specworks-specify <ref>`.
- Only this half: the `[code]` tasks and the code gate. Do not write or read
  this change's `@ac` tests, tick `[test]` tasks or run `gate test`.
- No scope creep: no features, refactors or clean-ups the tasks do not ask
  for. Note ideas for later instead.
- Tick a task only after its verification passed; never tick ahead.
- `@req` tags mark real implementations, never stubs or unrelated code.
- Re-read specs, design and tasks from disk before relying on them; the user
  may have edited them.
