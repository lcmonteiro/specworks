---
name: specworks-test
description: Test phase of spec-driven development - turn a change's acceptance criteria into failing tests (tagged @ac) and define the public API as stubs, before any implementation. Use when a change has been proposed and the user wants to write the tests first, define the interfaces/APIs, or says "test", "write the tests", "TDD" or "specworks test".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx:*), Read, Grep, Glob, Write, Edit
---

Test phase: write the tests that prove each acceptance criterion, and the API
stubs they call, so the implement phase has a precise, executable target.
At the end every acceptance criterion has at least one test tagged
`@ac <AC-ID>`, and those tests **fail for the right reason** (not implemented
yet), not because they cannot compile or import.

It is the third phase of `refine → propose → test → implement → review → verify → close`.

**Phase boundary**: write tests and API stubs only. A stub has the real public
signature (names, parameters, types, docs) and a body that only signals "not
implemented". No behaviour, no partial logic, even if it looks easy. When the
gate passes, stop and suggest `/specworks-implement`.

**Running the CLI**: use `specworks <cmd>`. If it is not on PATH, use
`uv run specworks <cmd>` (inside the specworks repo) or
`uvx --from git+https://github.com/lcmonteiro/specworks specworks <cmd>`.

---

## Steps

1. **Pick the change and check the plan is ready**

   ```bash
   specworks context --json
   specworks gate propose --change "<ref>"
   ```

   - Select the change as in `/specworks-propose` (named by the user, or the
     single active one; ask if ambiguous). Announce `Using change: <ref>`.
   - If `gate propose` fails, stop: show the failing checks and suggest
     `/specworks-propose <ref>` to finish the plan. Tests built on a broken plan
     test the wrong thing.
   - Otherwise move the change to this phase:
     ```bash
     specworks phase "<ref>" test
     ```
   - `commands.test` in the context is how this project runs its tests. If it
     is empty, find the test command from the repository (pyproject, package.json,
     go.mod, Cargo.toml, CMake, Makefile, CI config), confirm it with the user,
     and suggest adding it under `commands:` in the config.

2. **Load the plan and the project's test conventions**

   Re-read from disk:
   - the delta specs (`specs/**/spec.md`): every ADDED and MODIFIED requirement
     and its acceptance criteria, and every REMOVED requirement;
   - `design.md`, above all **Interfaces**: the public APIs, data shapes and
     CLI surfaces to stub and test against;
   - the pending tasks: `specworks task list --change "<ref>" --pending`.

   Then study the existing tests next to the code each capability owns
   (`codePath` from `specworks spec show <ref> --json`): framework, folder
   layout, file and test naming, fixtures, helpers, how I/O, time and network
   are faked. New tests follow these conventions.

   Find the tests that already cover MODIFIED or REMOVED criteria:
   ```bash
   specworks trace --change "<ref>" --json
   ```
   (rows with `tests` for those IDs).

3. **Define the API stubs**

   For each interface in design.md that does not exist yet, create it in the
   owning capability's code path, in the project's language and style:
   - real names, parameters, return and error types, and doc comments that
     cite the requirement IDs they serve (`Implements REQ-AUTH-003.`);
   - a body that only signals "not implemented" in the language's idiom
     (`raise NotImplementedError`, `throw new Error("not implemented")`,
     `panic("not implemented")`, `todo!()`, `= delete`/`assert(false)`...);
   - the minimum wiring for tests to reach it (exports, module registration,
     route declarations), nothing more.

   Do not add `@req` tags to stubs: `@req` marks implemented code and is added
   in the implement phase. If an interface in design.md is ambiguous enough to
   change what the tests assert, ask the user, and record the answer in
   design.md.

4. **Write the tests, one acceptance criterion at a time**

   For each ADDED or MODIFIED acceptance criterion:
   - Write at least one test that checks exactly what its WHEN/THEN says,
     through the public interface (black box): GIVEN → arrange, WHEN → act,
     THEN → assert. Cover error scenarios with the real error type or status.
   - Put the tag in a comment right above the test, in the language's comment
     syntax, and name the test after the criterion:
     ```python
     # @ac AC-AUTH-003.2
     def test_ac_auth_003_2_expired_link_is_rejected(): ...
     ```
     ```ts
     // @ac AC-AUTH-003.2
     it("AC-AUTH-003.2 rejects an expired link", ...)
     ```
     One test may carry several `@ac` tags when it truly checks several criteria.
   - Pick the level the criterion needs: unit for logic, integration for
     storage, APIs and wiring, end-to-end only when the criterion is about the
     whole flow.
   - Keep tests deterministic: control time, randomness, network and
     filesystem the way the project already does.

   MODIFIED criteria: update the existing tests found in step 2 to the new
   behaviour and keep their `@ac` tags. REMOVED requirements: delete their
   tests (they would fail once the behaviour is removed) and say which ones.

5. **Run the tests and confirm they fail for the right reason**

   Run `commands.test` (narrow it to the new tests when the suite is slow).
   Expected:
   - every new or updated test **fails**, because the stub is not implemented
     or the assertion does not hold yet;
   - **no** syntax, compile, import or collection errors: fix those now, they
     are bugs in the tests or stubs, not "red";
   - unrelated existing tests still pass.

   A test that already passes either checks nothing new or the behaviour
   already exists: look at it, then strengthen the test or tell the user.
   Never weaken an assertion, skip a test or mark it expected-to-fail to get
   the right colour.

6. **Tick the test tasks, gate and trace**

   ```bash
   specworks task done <N.M> [<N.M> ...] --change "<ref>"   # the test-writing tasks you completed
   specworks gate test --change "<ref>"
   specworks trace --change "<ref>" --write
   ```

   Fix every failing blocking check (an untested criterion, a tag with a
   wrong ID) and re-run. Warnings: fix them or explain them.

7. **Report and stop**

   Show a table, one row per acceptance criterion:

   ```
   Criterion       Test                                              Result
   AC-AUTH-003.1   tests/test_reset.py::test_ac_auth_003_1_request   fails: NotImplementedError
   AC-AUTH-003.2   tests/test_reset.py::test_ac_auth_003_2_expired   fails: NotImplementedError
   ```

   plus the stubs created (file and signature), tests updated or deleted for
   MODIFIED/REMOVED criteria, and anything you had to decide. Mention that the
   test suite is red on purpose until the implement phase. End with: "When
   you are ready, run `/specworks-implement <ref>` to make these tests pass."

---

## Guardrails

- No implementation: stubs only signal "not implemented". Behaviour belongs to
  `/specworks-implement`.
- Tests verify the acceptance criteria as written. If a criterion is wrong,
  ambiguous or untestable, stop and suggest `/specworks-propose <ref>` to fix
  the spec instead of testing your own interpretation.
- IDs come from the specs. Never invent an AC ID or tag a test with an ID of
  another change.
- Do not skip, disable, or mark tests as expected failures, and do not loosen
  assertions, to reach the expected state.
- Re-read the specs, design and tasks from disk before using them.
