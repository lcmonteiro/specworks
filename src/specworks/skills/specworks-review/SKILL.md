---
name: specworks-review
description: Review phase of spec-driven development - compare a change's code with its specs in both directions, find drift (behaviour no requirement describes, requirements the code misses, tests that do not really check their criterion, wrong tags), fix the code or update the spec with the user, and record every decision in review.md. Use after implementing a change, or when the user says "review", "sync code and spec", "check for drift" or "specworks review".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Read, Grep, Glob, Write, Edit
---

Review phase: make the code and the specs say the same thing. Implementation
always teaches something the plan did not know; this phase decides, for each
difference, whether the code or the spec is right, fixes the other one, and
records the decision in `review.md`.

It is the sixth phase of `refine → propose → interface → test → implement → review → verify → close`.

**Phase boundary**: this phase may change code, tests and the change's delta
specs, but only to remove drift. New features are out of scope: note them for a
future change. Every spec change and every accepted difference is agreed with
the user. When the gate passes, stop and suggest `/specworks-verify`.

**Running the CLI**: use `specworks <cmd>`. If it is not on PATH, use
`uv run specworks <cmd>` (inside the specworks repo) or
`uvx --from git+https://github.com/lcmonteiro/specworks specworks <cmd>`.

---

## Steps

1. **Pick the change and check it is implemented**

   ```bash
   specworks context --json
   specworks gate implement --change "<ref>"
   ```

   Select the change as the other phases do and announce `Using change: <ref>`.
   If `gate implement` fails (pending tasks, failing tests), stop and suggest
   `/specworks-implement <ref>`; reviewing unfinished work finds noise. Then:
   ```bash
   specworks phase "<ref>" review
   ```

2. **Collect the drift candidates**

   ```bash
   specworks review --change "<ref>" --json          # add --base <branch> if the default is wrong
   ```

   - spec → code: `reqWithoutCode`, `acWithoutTests`, `removedStillTagged`,
     `unknownTags`;
   - code → spec: `untracedSource` (changed code with no `@req`) and
     `untracedTests` (changed tests with no `@ac`).

   They are candidates. The real review is reading the code.

3. **Read the diff against the specs, in both directions**

   ```bash
   git diff <base>...HEAD     # plus uncommitted changes: git diff, git status
   ```

   Re-read the delta specs and design.md from disk, then check:
   - **Each requirement and criterion → code**: does the tagged code do exactly
     what the requirement says, including errors, limits and edge cases in the
     scenarios? Is anything only partly done?
   - **Each change in the code → spec**: is every new or changed behaviour
     (inputs accepted, outputs, errors, side effects, defaults, limits) covered
     by a requirement? Untagged code is either plumbing for a tagged
     requirement, a pure refactor, or behaviour the spec is missing.
   - **Each test → its criterion**: does it assert the THEN, through the public
     interface, and would it fail if the behaviour broke? A test that asserts
     too little is a finding.
   - **Tags**: on the code that really implements the requirement, none
     missing, none to wrong IDs.
   - **Design**: decisions in design.md the code does not follow (or that the
     code proved wrong).
   - **Quality that matters**: security, data loss, error handling or obvious
     bugs in the changed code, even when no spec covers them.

4. **Decide each finding with the user**

   Classify each one (`spec-gap`, `code-gap`, `test-gap`, `tag`, `quality`).
   For a disagreement between code and spec, say what the code does, what the
   spec says, and recommend which is right; then ask. Group small, obvious
   ones to keep the questions few. Then apply the decision:
   - **code fixed**: change the code (and its tests), run
     `specworks run test --change "<ref>"`;
   - **spec updated**: edit the change's delta spec (ADDED for new behaviour
     with the next free ID from `specworks spec show <cap> --json`, MODIFIED
     with the whole block), add the test (`@ac`) and tag (`@req`) for it, add
     or tick a task, and run `specworks validate --change "<ref>"`;
   - **accepted**: only with the user's explicit agreement, with the reason.

5. **Write `review.md`**

   ```bash
   specworks instructions review --change "<ref>" --json
   ```

   Follow `template` and `instruction`: every finding as `- [x] R<n>` with its
   type, IDs, location and Decision (`- [ ] R<n>` only while still open), and
   every file from `untracedSource` / `untracedTests` under "Changed files
   without tags" with why it needs no tag or which finding covers it.

6. **Gate and trace**

   ```bash
   specworks gate review --change "<ref>"            # same --base as step 2
   specworks trace --change "<ref>" --write
   ```

   The gate checks: valid specs, `review.md` written with no open finding,
   every requirement with code and every criterion with a test, no unknown
   tags, removed requirements gone, every untagged changed file accounted for,
   and the test suite passing. Fix and re-run until it passes.

7. **Report and stop**

   Summarize the findings by type and decision, the spec changes (IDs added or
   modified), the code changes, and anything accepted. End with: "When you are
   ready, run `/specworks-verify <ref>` for the final check before closing."

---

## Guardrails

- Never change a spec silently: every spec update and every accepted
  difference is agreed with the user and recorded in review.md.
- Fix drift, do not add features. Out-of-scope ideas go in the summary as
  candidates for a new change.
- Do not weaken tests or delete failing ones to pass the gate.
- Keep IDs stable: a changed behaviour is a MODIFIED requirement with the same
  ID; new behaviour gets the next free ID.
- Re-read specs, design, tasks and review.md from disk before relying on them.
