---
name: specworks-validate
description: Validate phase of spec-driven development - a final, read-only pass/fail check that a change is complete, correct and coherent before it is closed, with every failure pointing to the phase that fixes it. Use when a specworks change has been reviewed and the user wants to know if it is ready, or says "validate the change", "is the change ready to close" or "specworks validate".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Read, Grep, Glob
---

Validate phase: decide, without changing anything, whether the change is ready
to close. The CLI checks what can be measured; you check what needs reading.
The result is a clear PASS or FAIL, and every failure says which phase fixes
it.

It is the seventh phase of `refine → specify → design → test → code → review → validate → close`.

**Phase boundary**: read-only. Do not edit code, tests, specs, tasks, design or
review.md, and do not fix what you find, even when it is a one-line fix: report
it and point to the phase that owns it. The only write allowed is moving the
change's phase marker. On PASS suggest `/specworks-close`; on FAIL, the phase to
go back to.

<!-- specworks:include running-cli -->

<!-- specworks:include picking-the-change -->

---

## Steps

1. **Pick the change and start the phase once it is reviewed**

   Pick the change (above), then:
   ```bash
   specworks start validate --change "<ref>"      # same --base as below if the default is wrong
   ```
   It runs `gate review` (and the gates of any earlier phase left behind) and
   moves the change to validate only if they pass. If one fails, the verdict
   is FAIL: show the failing checks, suggest the skill of the failed gate's
   phase (`/specworks-review <ref>` for `gate review`), and stop.

2. **Run the measurable checks**

   ```bash
   specworks validate --change "<ref>" --json      # add --base <branch> if the default is wrong
   ```

   It runs the project's test, lint and typecheck commands and reports three
   groups; each failed check has a `fix` (the phase skill that owns it):
   - **Completeness**: proposal, specs and tasks exist; every task done; every
     requirement has `@req` code; every criterion has an `@ac` test; review done
     (`review.md` with no open finding).
   - **Correctness**: specs valid; tests, lint and typecheck pass; no tags to
     unknown IDs; removed requirements gone.
   - **Coherence**: every untagged changed file accounted for in `review.md`;
     diagram SVGs up to date; the change went through review.

3. **Check what needs reading (still read-only)**

   Re-read the delta specs, design.md, review.md and the diff
   (`git diff <base>...HEAD`). For each requirement, sample its `@req` code and
   the `@ac` tests of its criteria (`specworks trace --change "<ref>" --json`):
   - does each test exercise its scenario's WHEN and assert its THEN?
   - does the code follow the design decisions, or did review.md record why not?
   - is each `accepted` decision in review.md backed by a reason?
   - is anything in the diff clearly outside the change's scope?

   Report each problem as CRITICAL (the spec is not met, or a check above is
   unreliable) or WARNING (worth fixing, does not block), with the file and
   the phase that fixes it. Do not report taste.

4. **Report the verdict and stop**

   ```
   Validate <ref>: PASS | FAIL

   Completeness  5/5   Correctness  6/6   Coherence  3/3
   CRITICAL  every requirement has code: REQ-AUTH-002   -> /specworks-code
   WARNING   AC-AUTH-003.2 test checks the status only  -> /specworks-review
   ```

   - **PASS** (no critical issue from the CLI or from your reading): "Ready to
     close. Run `/specworks-close <ref>` to merge the specs into the living docs
     and archive the change."
   - **FAIL**: list the critical issues grouped by the phase to go back to, and
     suggest the earliest one (e.g. `specworks phase code --change "<ref>"`, then
     `/specworks-code <ref>`). Warnings are listed but do not block.

---

## Guardrails

- Never modify the project in this phase. A fix here would skip the review
  and the records the other phases keep.
- A FAIL from `specworks validate` is never overridden by your judgement; your
  reading can only add issues.
- Be specific: every issue names the check or file and the phase that fixes it.
- Re-read artifacts from disk; the user may have changed them since review.
