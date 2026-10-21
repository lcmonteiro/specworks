---
name: specworks-done
description: Finish a reviewed change in one run - validate it (the read-only PASS/FAIL check) and, only when it passes, close it (merge its specs into the living docs and archive it), running each phase's own skill in order. Use when a specworks change has been reviewed (a feature, a fix or a baseline-<capability>) and the user wants to finish it, or says "done", "finish the change", "validate and close" or "specworks done".
---

Done: take a reviewed change through **validate → close** in one run. The
change is closed only if validate passes: a FAIL stops here, with every
failure pointing to the phase that fixes it. Each phase is done exactly as
its own skill says; this skill only chains them, so `/specworks-done <ref>`
ends where `/specworks-validate <ref>` followed by `/specworks-close <ref>`
ends. It adds no check of its own and skips none.

It covers the last two phases of `refine → specify → design → test → code → review → validate → close`.

**Phase skills**: `specworks-validate` and `specworks-close`, installed next
to this skill (`../specworks-<phase>/SKILL.md`). Read each one when its phase
starts and follow its steps, checks and guardrails, including every point
where it asks the user (the merge plan in close). Skip only validate's final
"Report the verdict and stop": show the verdict and go on to close (step 3).

**Boundary**: validate changes nothing; close edits only the living docs
and, for new capabilities, the config. A failure is never fixed here: it
goes back to the phase that owns it.

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
  If several could fit, offer them as numbered options (the most
  recent recommended); if none fits, ask for its name. Announce `Using change: <ref>` and use
  that `<ref>` in every command.

---

## Steps

1. **Pick the change**

   Pick the change (above) and say the plan: `Done <ref>: validate → close`.
   Whatever phase the change is in, start with validate (step 2): its first
   step decides, as it does on its own, whether the change can enter
   validate (a change not yet reviewed fails there).

2. **Validate**

   Announce `Done · validate`, then follow `specworks-validate` (it starts
   the phase, runs `specworks validate` and reads what the CLI cannot check).

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

   Announce `Done · close`, then follow `specworks-close` (it starts the
   phase, which runs the validate gate again on the same code, registers new
   capabilities, shows the merge plan and waits for the user's go-ahead,
   updates the living design, then merges and archives).

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
  running both phases in one go does not skip it.
- If the user stops after validate, the change stays in `validate`;
  `/specworks-close <ref>` or `/specworks-done <ref>` finishes it later.
