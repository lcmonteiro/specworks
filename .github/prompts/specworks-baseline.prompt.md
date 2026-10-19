---
description: Baseline one capability of a project that already has code - record the behaviour the code already has as requirements, tie them to the existing tests and code with @ac / @req tags, and hand the change over to close so the capability gets its living spec. No behaviour change. Use after /specworks-adopt, once per capability (each baseline closed before the next), whenever a specworks capability has no living spec yet, or when the user says "baseline", "baseline <capability>", "record what <capability> does today" or "specworks baseline".
agent: agent
---

Baseline: record the behaviour one capability already has, so later changes
can MODIFY its requirements instead of only ADDING them. A baseline is an
ordinary change named `baseline-<capability>` whose specs ADD the existing
behaviour. Its tests and code exist, so the test and code phases only add
tags; `/specworks-close` then writes the living spec exactly as for any other
change.

**One capability per run.** After `/specworks-adopt`, the capabilities are
baselined one after another, each closed before the next:

```
for each capability:
    /specworks-baseline <capability>
    /specworks-close baseline-<capability>
```

**Boundary**: a baseline changes no behaviour. It writes a change folder and
adds comment tags (and tests only for criteria no test covers); it never
fixes the code, even a bug it finds.

**Running the CLI**: use `specworks <cmd>`. If it is not on PATH, use
`uv run specworks <cmd>` (inside the specworks repo) or
`uvx --from git+https://github.com/lcmonteiro/specworks specworks <cmd>`.
Gates and `validate` reuse a test/lint/typecheck result from the same code
(`same code as the run at ...`). After fixing something outside the code (a
git-ignored file, a service the tests need), run `specworks run <key>` once:
its result replaces the reused one. `--fresh` on a gate, `start` or `validate`
does the same for that command.

---

## Steps

1. **Pick the capability**

   ```bash
   specworks context --json
   ```

   - `"root": null`, or no capabilities: the project is not adopted yet.
     Stop and offer `/specworks-adopt`, which sets it up and maps the
     capabilities.
   - The capability is the one the user named. Otherwise list them:
     ```bash
     specworks spec list
     ```
     and propose the first one with 0 requirements (no living spec yet),
     in the order of the list; go on once the user confirms or picks
     another. When every capability has requirements, say so and stop.
   - A capability that is not registered: stop and offer
     `/specworks-adopt` (or `specworks capability add`) first.
   - A change `baseline-<capability>` already in `changes`: continue it
     from its phase (`specworks status --change "baseline-<capability>"`)
     instead of creating a new one.

2. **Check the capability and create the change**

   ```bash
   specworks spec show "<capability>" --json
   ```

   A capability with requirements already has a living spec: it needs no
   baseline (offer `/specworks-refine` for what is missing).

   The test suite must be green: the design and code gates require it, and a
   red suite cannot show that the baseline matches the code. Check it first:
   ```bash
   specworks run test
   ```
   If it fails, stop before creating anything: name the failing tests and
   suggest fixing them first, in their own change (`/specworks-refine`), or
   baselining a capability whose tests pass. Never narrow `commands.test`
   to hide the failures.

   Otherwise, preferably on a new branch (review compares the branch with
   its base):
   ```bash
   specworks new "baseline-<capability>" --json
   specworks phase specify --change "baseline-<capability>"
   ```
   (`--module <m>` on `new` for a capability of another module.) Announce
   `Using change: <ref>` and use that `<ref>` in every command.

3. **Read the behaviour**

   Read the capability's code and its tests; requirements come from both:
   - existing tests: each one asserts behaviour someone decided on;
   - the code: public entry points, validation, error handling and side
     effects, including behaviour no test checks yet;
   - the README, docs, comments and changelog, to name and explain them.

   Record only observable behaviour (inputs, outputs, errors, side effects),
   not how the code does it. Keep a list of what looks like a bug or is
   unclear: it is not specified here (step 4).

4. **Write proposal, delta spec and tasks**

   Use `specworks instructions proposal|specs|tasks --change "<ref>" --json`
   as `/specworks-specify` does, with these differences:
   - `proposal.md`: Why = "record the existing behaviour of `<capability>`";
     What Changes = "no behaviour change"; the capability under Modified
     Capabilities (it is registered); Out of Scope = the suspected bugs and
     unclear behaviour from step 3, each as a candidate for its own change.
   - The delta spec starts with `## Purpose` (one or two sentences: the
     capability has no living spec yet), then only `## ADDED Requirements`,
     IDs from `nextId`.
     Prefer fewer, meaningful requirements. A criterion read from the code
     alone is as valid as one a test shows; step 6 gives it a test, so
     do not mark it in the spec.
   - `tasks.md`: per requirement, one task to tag the tests that check its
     criteria (`@ac`) and to write a test for any criterion with none, and
     one task to tag the code that implements it (`@req`).

   ```bash
   specworks check --change "<ref>"
   ```

   Show the requirements and criteria table as `/specworks-specify` step 5
   does, with the source of each (the test that shows it, or `code only:
   <file>` for one that gets a new test in step 6), and the
   list of suspected bugs. **Stop and wait** for the user to confirm: a
   baseline that records a bug as a requirement makes the bug the spec.

5. **Gate specify and record the API as unchanged**

   ```bash
   specworks trace --change "<ref>" --write
   specworks start design --change "<ref>"
   ```
   Write `design.md` with only:
   ```markdown
   ## Interfaces

   None: a baseline records existing behaviour and changes no API.
   ```

6. **Tag the tests**

   ```bash
   specworks start test --change "<ref>"
   ```
   Add `@ac <ID>` comments to the existing tests that check each criterion
   (one tag may list several IDs). Write a new test only for a criterion
   that none covers; it must pass against the current code (if it fails,
   the criterion is wrong or it is a bug: back to step 4, not a code fix).
   Tick the test tasks: `specworks task done --change "<ref>" <N.M>`.

7. **Tag the code**

   ```bash
   specworks start code --change "<ref>"
   ```
   Add `@req <ID>` comments where each requirement is implemented (the
   function or class that decides the behaviour, not every caller). Change
   nothing else. Tick the code tasks.

8. **Review and validate**

   ```bash
   specworks start review --change "<ref>"
   specworks review --change "<ref>" --json
   ```
   Write `review.md` (`specworks instructions review --change "<ref>" --json`).
   The only changed files should be tests and code that gained tags (and any
   new test); a code change other than a tag is a finding. Then:
   ```bash
   specworks start validate --change "<ref>"
   specworks validate --change "<ref>"
   ```
   Every failure names the step to go back to.

9. **Hand over to close**

   Show the summary: requirements and criteria recorded, tests tagged and
   added, files tagged, the suspected bugs left out. End with:
   "The baseline of `<capability>` passes validate. Run `/specworks-close
   baseline-<capability>` to write its living spec; then
   `/specworks-baseline` for the next capability. The suspected bugs can
   each start with `/specworks-refine`."

---

## Guardrails

- One capability per change, closed before the next one starts.
- Never change behaviour: no refactors, no bug fixes, no renames. A bug is
  reported (Out of Scope), not fixed.
- The user confirms the requirements and criteria before anything is tagged.
- Capability names, prefixes, IDs and delta paths come from the CLI
  (`spec show`, `instructions`), never invented.
- Record behaviour the code has, not behaviour it should have: what it
  should do is a new change, through `/specworks-refine`.
- Never edit the living docs (`<path>/<docs_dir>/`) by hand: `close` writes
  them.
