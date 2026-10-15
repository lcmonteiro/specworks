---
name: specworks-code
description: Code phase of spec-driven development - work through a change's tasks, replacing the API stubs with real code until the acceptance tests pass, tagging code with @req and ticking tasks as they are done. Use when a specworks change has its failing tests and the user wants to implement it, or says "implement the change", "make the acceptance tests pass" or "specworks code".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Read, Grep, Glob, Write, Edit
---

Code phase: make the failing tests from the test phase pass by writing
the code the tasks describe, and nothing more. Every requirement ends up with
code tagged `@req <REQ-ID>`, every task ticked, and the whole test suite green.

It is the fifth phase of `refine → specify → design → test → code → review → validate → close`.

**Phase boundary**: implement what the specs and tasks say. The specs, the
acceptance criteria and the tests from the test phase are the contract: do not
change them to make the code easier. When the gate passes, stop and suggest
`/specworks-review`.

<!-- specworks:include running-cli -->

<!-- specworks:include picking-the-change -->

---

## Steps

1. **Pick the change and start the phase once the tests are in place**

   - Pick the change (above), then:
     ```bash
     specworks start code --change "<ref>"
     ```
     It runs `gate test` and moves the change to code only if it passes.
   - If it fails because criteria have no tests, stop and suggest
     `/specworks-test <ref>`. If the user explicitly wants to implement without
     tests first, say what that loses (no executable proof per criterion) and
     go on only with their agreement, moving the change by hand:
     `specworks phase "<ref>" code`.
   - `commands` in the context are this project's tools; `specworks run test`
     (and `run lint`, `run typecheck` when configured) runs them in the right
     folder. If `test` is not configured, find it, confirm it with the user and
     suggest adding it under `commands:`.

2. **Load the plan**

   Re-read from disk: the delta specs, `design.md` (decisions and interfaces),
   and the tasks:
   ```bash
   specworks task list --change "<ref>" --pending
   specworks trace --change "<ref>" --json
   ```
   `trace` shows which tests cover each criterion and where the stubs and
   existing code are tagged.

3. **Work through the tasks, in order, one at a time**

   For each pending task:
   1. Say which task you are on (`Task 2.1: ...`).
   2. Read the requirements and criteria it names, the tests that cover them,
      and the code around the change.
   3. Write the smallest code that makes those tests pass the way the
      requirement intends, in the project's style; follow design.md's
      decisions. Replace stubs with real code.
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
      tests were removed in the test phase).
   6. Run the relevant tests, then the suite when the task is done:
      ```bash
      specworks run test --change "<ref>"
      ```
   7. Tick the task only when its verification passes:
      ```bash
      specworks task done <N.M> --change "<ref>"
      ```

   **Pause and ask** instead of guessing when:
   - a task or requirement is unclear, or two of them conflict;
   - the tests and the spec disagree, or a test looks wrong: a test may only
     change if it contradicts its acceptance criterion, and then with the
     user's agreement, and you say so in the report;
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

   Fix what fails. Never skip, disable or loosen tests to get green.

5. **Gate and trace**

   ```bash
   specworks gate code --change "<ref>"
   specworks trace --change "<ref>" --write
   ```

   The gate checks that the specs are still valid, every task is ticked,
   every requirement has `@req` code, every criterion still has a test, no
   tag points to an unknown ID, removed requirements are gone, and the test
   suite passes (it runs `commands.test`). Fix every failing check and re-run.

6. **Report and stop**

   Summarize: tasks done, files changed per capability, where each
   requirement is implemented (from the trace), test results, any decision
   or deviation recorded in design.md, and any test changed with the user's
   agreement. End with: "When you are ready, run `/specworks-review <ref>` to
   check the code and the specs agree."

---

## Guardrails

- The specs and tests are the contract. Do not edit the delta specs here; if
  they are wrong, stop and suggest `/specworks-specify <ref>`.
- No scope creep: no features, refactors or clean-ups the tasks do not ask
  for. Note ideas for later instead.
- Tick a task only after its verification passed; never tick ahead.
- `@req` tags mark real implementations, never stubs or unrelated code.
- Re-read specs, design and tasks from disk before relying on them; the user
  may have edited them.
