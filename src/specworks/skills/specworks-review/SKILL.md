---
name: specworks-review
description: Review phase of spec-driven development - compare a change's code with its specs in both directions, find drift (behaviour no requirement describes, requirements the code misses, tests that do not really check their criterion, an API or design the code proved wrong, wrong tags), propose for each one a change to the code, the spec or the design/API, apply it with the user or send the change back to the phase that owns it, and record every decision in review.md. Use after implementing a change, or when the user says "review", "sync code and spec", "check for drift" or "specworks review".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Read, Grep, Glob, Write, Edit
---

Review phase: make the code, the specs and the design (API) say the same
thing. Implementation always teaches something the plan did not know; this
phase decides, for each difference, which one is right and proposes the
change to the others: the **code**, the **spec** or the **design/API**.
Small, local changes are applied here with the user; larger ones send the
change back to the phase that owns them. Every decision goes in `review.md`.

It is the sixth phase of `refine → specify → design → test → code → review → validate → close`.

**Phase boundary**: this phase may change code, tests, the change's delta
specs and design.md, but only to remove drift, and only in small, local
steps. Larger changes go back to `/specworks-specify`, `/specworks-design`
or `/specworks-code`. New features are out of scope: note them for a future
change. Every spec, design or API change and every accepted difference is
agreed with the user. When the gate passes, stop and suggest
`/specworks-validate`.

**Running the CLI**: use `specworks <cmd>`. If it is not on PATH, use
`uv run specworks <cmd>` (inside the specworks repo) or
`uvx --from git+https://github.com/lcmonteiro/specworks specworks <cmd>`.

---

## Steps

1. **Pick the change and check it is implemented**

   ```bash
   specworks context --json
   specworks gate code --change "<ref>"
   ```

   Select the change as the other phases do and announce `Using change: <ref>`.
   If `gate code` fails (pending tasks, failing tests), stop and suggest
   `/specworks-code <ref>`; reviewing unfinished work finds noise. Then:
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
   - **Design / API**: does the code expose exactly the interfaces under
     `## Interfaces` in design.md (names, parameters, return and error types,
     files)? Does it follow the Decisions? Where it differs, which one is
     right: did the code drift, or did implementing it prove the agreed API or
     decision wrong (awkward to call, leaking internals, missing an error,
     impossible to test)?
   - **Quality that matters**: security, data loss, error handling or obvious
     bugs in the changed code, even when no spec covers them.

4. **Propose a change for each finding and decide it with the user**

   Classify each one (`spec-gap`, `code-gap`, `design-gap`, `test-gap`, `tag`,
   `quality`). For a disagreement, say what the code does, what the spec and
   design.md say, and **propose the change**: to the code, to the spec, or to
   the design/API, with what exactly would change. Then ask. Group small,
   obvious ones to keep the questions few.

   Apply it here when it is small and local; otherwise send the change back:

   | Change to | Here (small, local) | Back to (larger) |
   |---|---|---|
   | **code** | fix the code and its tests, run `specworks run test --change "<ref>"` | `/specworks-code`: a requirement is far from done |
   | **spec** | edit the delta spec (ADDED with the next free ID from `specworks spec show <cap> --json`, MODIFIED with the whole block), add its test (`@ac`), tag (`@req`) and task, run `specworks check --change "<ref>"` | `/specworks-specify`: several requirements, a new capability, or the proposal's scope changes |
   | **design / API** | one interface, no other callers: update `## Interfaces` (or the Decision) in design.md, the code and its tests together, run the tests | `/specworks-design`: the API changes for other callers or several interfaces; test and code follow again |

   To send it back: record the finding as open with the agreed proposal, then
   ```bash
   specworks phase "<ref>" <specify|design|code>
   ```
   and suggest the matching skill. When the change comes back to review,
   check that the proposal was carried out and close the finding.
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
   modified), the design/API changes, the code changes, anything accepted, and
   any change sent back to an earlier phase (then stop there instead of
   suggesting validate). End with: "When you are
   ready, run `/specworks-validate <ref>` for the final check before closing."

---

## Guardrails

- Never change a spec or an API silently: every spec, design or API update
  and every accepted difference is agreed with the user and recorded in
  review.md.
- Fix drift, do not add features. Out-of-scope ideas go in the summary as
  candidates for a new change.
- Do not weaken tests or delete failing ones to pass the gate.
- Keep IDs stable: a changed behaviour is a MODIFIED requirement with the same
  ID; new behaviour gets the next free ID.
- Re-read specs, design, tasks and review.md from disk before relying on them.
