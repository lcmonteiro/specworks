---
name: specworks-build
description: Build a specified change end to end in cycles of design → test → code → review, running each phase's own skill in order; after each review with findings, ask whether to start a new cycle and start it from the earliest phase the findings need (code findings → code, review; test findings → test, code, review; design/API findings → design, test, code, review). Use when a specworks change has been specified and the user wants to build it in one go, or says "build the change", "run the build cycle", "design test code review" or "specworks build".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Read, Grep, Glob, Write, Edit, Agent
---

Build: take a specified change through **design → test → code → review** in
one run, then repeat the part of that cycle the review findings need until
the review is clean (or the user stops). Each phase is done exactly as its
own skill says; this skill only chains them and decides where a new cycle
starts.

It covers phases three to six of `refine → specify → design → test → code → review → validate → close`.

**Phase skills**: `specworks-design`, `specworks-test`, `specworks-code` and
`specworks-review`, installed next to this skill (`../specworks-<phase>/SKILL.md`).
Each phase runs in its own subagent (below), which follows that skill's
steps, checks and guardrails. You do not do a phase's work yourself: you
start the subagents, ask the user what they return, write the answers to
disk, and decide where each cycle starts.

**Boundary**: the build stops, and does not work around it, when a phase gate
fails and cannot be fixed within that phase, when the specs turn out wrong
(spec findings go to `/specworks-specify`), or when the user says stop.

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

**Phases in subagents**: each phase runs in a fresh subagent that depends
only on the project and the change's artifacts on disk, never on this
conversation. You are the coordinator: you start the subagents, ask the user
their questions, and write the answers to disk.

- **The prompt is fixed**: start each phase with your subagent tool (Claude
  Code: `Agent`) and this prompt, with only `<phase>`, `<ref>` and the skills
  folder (the one holding this skill's folder, e.g. `.claude/skills`) filled
  in. Never add a summary of the conversation, an answer or a decision: what
  the phase needs from the user is on disk.
  ```
  Run the <phase> phase of the change <ref>: follow
  <skills folder>/specworks-<phase>/SKILL.md, reading only the project and
  the change's artifacts on disk. You cannot ask the user. When the skill
  would stop for the user, first write what you propose into your own
  artifact, then stop and return the question. Skip the skill's "Report and
  stop". End your last message with exactly one line:
  Result: done <one-line result; the gate passed>
  Result: question <the closing question as the skill asks it, options included>
  Result: blocked <what failed, and the phase or skill it goes back to>
  ```
- **On `Result: done`**: report its line and start the next phase.
- **On `Result: question`**: ask the user the question as it is. Write the
  answer where the next run of the phase reads it, then start a fresh
  subagent for the same phase with the same prompt:

  | Question | Where the answer goes |
  |---|---|
  | design: the API | design.md `## Interfaces`, as agreed |
  | test, code: the test command | `spec.yml` `commands:` (`test: <command>`) |
  | code: an unclear task, a test against the spec, new work | the Decision in design.md, or a new task in tasks.md |
  | review: each finding | the finding's `**Decision**:` line in review.md |

  Write only the answer, in the place the question is about. Never do the
  phase's own work.
- **On `Result: blocked`**: stop and report where and why, as for a gate
  that cannot be fixed.
- **No subagent tool**: follow the phase skill yourself in this
  conversation, and still write every answer to disk as above.

**In a build**, add this fixed line to every phase's prompt:
```
This phase runs inside /specworks-build: also follow step 2 (open review
findings from an earlier cycle) and, in review, step 3 (propose, do not fix)
of <skills folder>/specworks-build/SKILL.md.
```

---

## Steps

1. **Pick the change and where to start**

   Pick the change (above), then:
   ```bash
   specworks gate specify --change "<ref>"
   specworks status --change "<ref>" --json
   specworks cycle --change "<ref>" --json
   ```

   - If `gate specify` fails, stop and suggest `/specworks-specify <ref>`.
   - Start point:
     - a previous review left open findings (`cycle` returns `startAt`):
       resume with that cycle (step 4);
     - the change is already in `design`, `test`, `code` or `review`: resume
       at that phase;
     - otherwise start at `design`.
   - Say the plan, e.g. `Cycle 1: design → test → code → review`.

2. **Run the cycle's phases in order**

   For each phase of the cycle, announce `Cycle <n> · <phase>` and start its
   subagent (above). The phase skill moves the change with `specworks start`,
   does the work and runs its gate. On `Result: done`, report its line and
   start the next phase; on `Result: question`, ask, write the answer to disk
   and start a fresh subagent for the same phase; on `Result: blocked`, stop
   and report where and why.

   From the second cycle on, each phase works on the **open findings in
   review.md** that belong to it (`specworks cycle --change "<ref>" --json`
   lists each finding with its phase): carry out the agreed proposal in the
   finding's Decision, plus whatever the later phases need to follow it (a
   new API needs its tests and code). A finding marked `done in <phase>:` has
   that phase's part done already (e.g. the spec change from specify): carry
   out what it means for this phase. Do not redo untouched work.

   If a gate fails, the phase fixes it as its skill says. If it cannot be
   fixed there (the specs are wrong, the user must decide something outside
   the build), the subagent returns `Result: blocked`: stop and report where
   and why.

3. **Review: propose, do not fix**

   The review subagent runs `specworks-review` as written, with one
   difference: in a build, every finding that needs work is recorded
   **open** with the phase that will carry it out, instead of being fixed
   inside review. It decides nothing with the user itself:

   - **First run**: it writes review.md with every finding open and the
     change it proposes, then returns them all in one `Result: question`
     (small, obvious ones grouped into one yes/no question, as review does):
     ```markdown
     - [ ] R2 **design-gap** `reset()` returns None; callers need the token (REQ-AUTH-003)
       - **Proposal**: back to design: return `ResetToken` from `ResetService.request_reset`
     ```
   - **You** ask the user about each finding, one at a time, and turn each
     answer into the finding's `**Decision**:` line in review.md: the
     proposal as agreed (`back to <phase>: ...`), the user's other choice,
     or `accepted: <reason>` with the box ticked. Spec findings
     (`spec-gap`) get `back to specify: ...`.
   - **Then** a fresh review subagent reads the decided review.md, ticks
     the findings from an earlier cycle that are now done (`- [x]`, with
     what was done), finishes the file and gates it.

   The gate is `specworks gate review --change "<ref>" --allow-open`: open
   findings do not fail it here (step 4 turns them into the next cycle), but
   every other check (tests pass, untagged files accounted for, tags, a known
   type or `back to <phase>:` on every open finding) must.

4. **After the review: ask about a new cycle**

   ```bash
   specworks cycle --change "<ref>"
   ```

   - **No open findings**: the build is done (go to step 5).
   - **A spec finding** (`handOver` is `/specworks-specify`): stop the build.
     Explain which requirement is missing or wrong, and offer:
     ```
     1. /specworks-specify <ref> (recommended): fix the specs; /specworks-build <ref> then continues
     2. Stop here
     ```
     Specify marks each finding it carried out `done in specify:
     ...`, so `cycle` then starts at design and the build resumes there.
   - **Otherwise** show the open findings and where each one is resolved,
     then ask:

     ```
     Review found 3 open findings:
       R1 code-gap    lockout counter not reset on success   -> code
       R2 design-gap  reset() should return the token        -> design
       R3 test-gap    AC-AUTH-003.2 only checks the status   -> test
     Start cycle 2 from design: design → test → code → review? (yes/no)
     ```

     - **Yes**: go back to step 2 with the next cycle number, starting at
       `startAt`; that phase's subagent moves the change back with
       `specworks start <startAt>`.
     - **No**: stop. The findings stay open in review.md; the user can run a
       single phase skill, or `/specworks-build <ref>` later to resume.

   The cycle starts at the earliest phase any finding needs: code findings
   (`code-gap`, `tag`, `quality`) → code, review; test findings → test, code,
   review; design/API findings → design, test, code, review. A
   `back to <phase>: ...` in a finding's Decision overrides its type, and a
   `done in <phase>: ...` line moves it on to the phase after that one.

   After the third cycle, say how many cycles have run and what keeps coming
   back before asking again: repeated findings usually mean the spec or the
   design needs a decision, not another cycle.

5. **Report and stop**

   Summarize per cycle: the phases run, the API agreed or changed, tests
   added, the code written, and the findings (found, resolved, accepted).
   Run `specworks trace --change "<ref>" --write`. Say "The build is
   complete." and end with:
   ```
   1. /specworks-done <ref> (recommended): validate, then close
   2. /specworks-validate <ref>: the final check alone
   3. Stop here
   ```

---

## Guardrails

- Every phase follows its own skill, in its own subagent: same steps, same
  gates, same questions to the user, asked by you. The build never skips a
  gate or a decision to keep going.
- A subagent's prompt is the fixed text above with the phase, the ref and
  the skills folder filled in: nothing from this conversation. What it needs
  from the user, it reads from disk.
- You write only the user's answers, in the place the question is about;
  never a phase's own work.
- A new cycle only starts after the user says yes, and only from the phase the
  open findings need.
- Spec problems are not fixed inside the build: hand over to
  `/specworks-specify`.
- Do not weaken tests, skip gates or mark findings resolved to finish a cycle.
