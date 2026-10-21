---
name: specworks-done
description: Finish a reviewed change in one run - validate it (the read-only PASS/FAIL check) and, only when it passes, close it (merge its specs into the living docs and archive it), running each phase's own skill in order. Use when a specworks change has been reviewed (a feature, a fix or a baseline-<capability>) and the user wants to finish it, or says "done", "finish the change", "validate and close" or "specworks done".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Read, Grep, Glob, Write, Edit, Agent
---

Done: take a reviewed change through **validate → close** in one run. The
change is closed only if validate passes: a FAIL stops here, with every
failure pointing to the phase that fixes it. Each phase is done exactly as
its own skill says; this skill only chains them, so `/specworks-done <ref>`
ends where `/specworks-validate <ref>` followed by `/specworks-close <ref>`
ends. It adds no check of its own and skips none.

It covers the last two phases of `refine → specify → design → implement (test | code) → review → validate → close`.

**Phase skills**: `specworks-validate` and `specworks-close`, installed next
to this skill (`../specworks-<phase>/SKILL.md`). Each phase runs in its own
subagent (below), which follows that skill's steps, checks and guardrails,
including every point where it asks the user (the merge plan in close): the
subagent returns the question and you ask it. You do not do a phase's work
yourself.

**Boundary**: validate changes nothing; close edits only the living docs
and, for new capabilities, the config. A failure is never fixed here: it
goes back to the phase that owns it.

<!-- specworks:include running-cli -->

<!-- specworks:include asking-the-user -->

<!-- specworks:include picking-the-change -->

<!-- specworks:include phase-subagents -->

**In a done run**, the phases add a fixed line to the prompt:
- validate: `End with the report of step 4 of the skill before the Result
  line: PASS is Result: done, FAIL is Result: blocked.`
- close, first run: `This phase runs inside /specworks-done: stop before
  step 4 of the skill. Return the capabilities to register (step 2) as the
  question, or, when none is left, the merge plan (step 3).`
- close, after the user's go-ahead on the merge plan, a second subagent with
  this line instead: `This phase runs inside /specworks-done: the merge plan
  is approved; continue from step 4 of the skill.`

---

## Steps

1. **Pick the change**

   Pick the change (above) and say the plan: `Done <ref>: validate → close`.
   Whatever phase the change is in, start with validate (step 2): its first
   step decides, as it does on its own, whether the change can enter
   validate (a change not yet reviewed fails there).

2. **Validate**

   Announce `Done · validate` and start its subagent (above), which will
   follow `specworks-validate`: it starts the phase, runs
   `specworks validate`, reads what the CLI cannot check, and returns
   validate's report with `Result: done` (PASS) or `Result: blocked` (FAIL).
   Validate changes nothing and asks nothing.

3. **Show the verdict and decide**

   Show validate's report exactly as its step 4 lays it out:
   ```
   Validate <ref>: PASS | FAIL

   Completeness  5/5   Correctness  6/6   Coherence  3/3
   WARNING   AC-AUTH-003.2 test checks the status only  -> /specworks-review
   ```
   - **FAIL** (a critical issue from the CLI or from your reading): stop.
     List the critical issues grouped by the phase to go back to, offer the
     earliest one as the recommended option (`specworks phase <phase>
     --change "<ref>"`, then `/specworks-<phase> <ref>`), with "Stop here" as
     the other, and say that `/specworks-done <ref>` finishes it once fixed.
     Nothing is closed.
   - **PASS**: list any warnings (they do not block) and go on to close.

4. **Close**

   Announce `Done · close` and start the first close subagent (above),
   which will follow `specworks-close`: it starts the phase (which runs the
   validate gate again on the same code) and returns a question:
   - **Register a capability** ("Register `<name>` in `<module>` at
     `<code path>`? (yes/no)"): ask the user, then write the answer to the
     project yourself (the user's module and path on no), and start the
     first close subagent again:
     ```bash
     specworks capability add <name> --path <code path> [--module <module>] [--prefix <P>] [--description "<one line>"]
     ```
   - **The merge plan** ("Merge and archive? (yes/no)"): ask the user. On
     yes, start the second close subagent (the merge plan is approved,
     continue from step 4): it updates the living design, merges and
     archives. On no, stop: nothing is written and the change stays in
     close.

5. **Report and stop**

   One summary for both phases:
   ```
   Done <ref>: closed

   Validate   PASS (2 warnings)
   Living docs  src/auth/docs/: spec.md, requirements.md, design.md
   Requirements  +2 added, 1 modified, 0 removed
   Archived   spec/changes/archive/2026-10-19-add-password-reset/
   ```
   Then end with close's next steps as numbered options: commit the living
   docs, the archive and the code together (and open a PR), and, for a
   `baseline-<capability>` change, the next capability to baseline
   (`/specworks-baseline <capability>`) or, when every capability has a
   living spec, the first waiting bug change; plus "Stop here".

---

## Guardrails

- Never close a change that fails validate, whatever the reason; your
  reading can add critical issues, never remove the CLI's.
- Never fix a failure here: no code, test or spec edits. Send it to the
  phase that owns it.
- The user's go-ahead on the merge plan (close step 3) is still required;
  running both phases in one go does not skip it. Only that go-ahead starts
  the second close subagent.
- A subagent's prompt is the fixed text above with the phase, the ref and
  the skills folder filled in: nothing from this conversation.
- If the user stops after validate, the change stays in `validate`;
  `/specworks-close <ref>` or `/specworks-done <ref>` finishes it later.
