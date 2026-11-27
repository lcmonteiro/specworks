---
name: specworks-autopilot
description: Run a specified change from its current phase (specify, design, implement, review or validate) to a passed validate on its own, chaining specify, the build and validate in subagents, taking the option marked (recommended) at each stop, logging every decision in autopilot.md, and stopping before close with the hard decisions for the user to validate. Use when a specworks change has been refined and the user wants the rest of the flow up to validate to run unattended, or says "autopilot", "run it on its own" or "specworks autopilot".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Read, Grep, Glob, Write, Edit, Agent
---

Autopilot: take a refined change from its current phase to a passed
validate in one unattended run. It chains the phases exactly as the
coordinators do (specify, then `/specworks-build`, then validate as in
`/specworks-done`), and where they would stop for the user it answers
itself, by the rules below, and logs the decision in `autopilot.md`. It
stops before close and hands the user the hard decisions to validate.

It covers phases two to six of `refine → specify → design → implement (test | code) → review → validate → close`.

**Phase skills**: `specworks-specify`, `specworks-build` (followed as a
coordinator, with its own phase skills) and `specworks-validate`, installed
next to this skill (`../specworks-<phase>/SKILL.md`). Each phase runs in its
own subagent (below), which follows that skill's steps, checks and
guardrails. You do not do a phase's work yourself: you start the subagents,
answer what they return, write the answers to disk and log them.

**Boundary**: Autopilot never runs in refine: refinement stays with the user.
Autopilot never runs close and never pushes. It skips no check and adds no
gate: each phase is done exactly as its own skill says, and autopilot only
answers its stops. It stops, and does not work around it, when a phase is
blocked, validate fails, or a question has no answer it can take.

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
  in (`<phase>` is the skill's name: `test` and `code` for the two halves of
  implement). Never add a summary of the conversation, an answer or a
  decision: what the phase needs from the user is on disk.
  ```
  Run the <phase> phase of the change <ref>: follow
  <skills folder>/specworks-<phase>/SKILL.md, reading only the project and
  the change's artifacts on disk. You cannot ask the user. When the answer
  to a question the skill would ask is already on disk, use it and go on; do
  not ask it again. When the skill would stop for the user, first write what
  you propose into your own artifact, then stop and return the question.
  Skip the skill's "Report and stop". End your last message with exactly
  one line:
  Result: done <one-line result; the gate passed>
  Result: question <the closing question as the skill asks it, options included>
  Result: blocked <what failed, and the phase or skill it goes back to>
  ```
- **On `Result: done`**: report its line and start the next phase.
- **On `Result: question`**: ask the user the question as it is. Write the
  answer where the next run of the phase reads it, then start a fresh
  subagent for the same phase with the same prompt (review in a build: see
  its step 3):

  | Question | Where the answer goes |
  |---|---|
  | design: the API | design.md `## Interfaces`: the subagent writes it with a line `Proposed: waiting for the user's agreement`; replace that line with `Agreed with the user` (and the user's changes) |
  | test, code: the test command | the config, written with `specworks config set commands.test "<command>"` |
  | code: an unclear task, an existing test against the spec, new work | the Decision in design.md, or a new task in tasks.md |
  | review: each finding | the finding's `**Decision**:` line in review.md, written with `specworks finding decide R<n> --change "<ref>" "<decision>"` |

  Write only the answer, in the place the question is about. Never do the
  phase's own work.
- **On `Result: blocked`**: stop and report where and why, as for a gate
  that cannot be fixed.
- **No subagent tool**: follow the phase skill yourself in this
  conversation, and still write every answer to disk as above.

In autopilot, "ask the user" in these rules means "answer by the rules of
step 2": you are the user at every stop, and you still write each answer
where the table above says it goes.

---

## Steps

1. **Pick the change and where to start**

   Pick the change (above), then:
   ```bash
   specworks status --change "<ref>" --json
   specworks cycle --change "<ref>" --json
   ```

   Read the phase and choose the run:

   | Phase in `specworks status` | Autopilot runs |
   |---|---|
   | `refine` | nothing: refuses, `/specworks-refine <ref>` or `/specworks-specify <ref>` |
   | `specify` | specify, then the build, then validate |
   | `design`, `implement`, `review` | the build, then validate |
   | `validate` | validate |
   | `close`, or a closed change | nothing: refuses, `/specworks-done <ref>` (close) |

   On a refusal, say why and offer the skill to run instead as the
   recommended option, with `Stop here`.

   Otherwise open `autopilot.md` in the change folder: create it with its
   header (step 3) when it is not there; when it is, this is a resumed run,
   so read its decisions and carry on from the phase on disk. Say the plan,
   e.g. `Autopilot <ref>: specify → build → validate, stopping before close`.

   - **Specify** (when the change is in specify): announce
     `Autopilot · specify` and start its subagent with the fixed prompt,
     `<phase>` set to `specify`. Answer its questions (step 2); an answer
     that has no place in the coordinators' table (the specify
     confirmation) is its entry in `autopilot.md`, which the restarted
     subagent reads with the change's other artifacts.
   - **The build**: follow ../specworks-build/SKILL.md as its coordinator
     from its step 1, with its fixed prompts and its in-a-build line, the
     test half in its own worktree and the merge as it says. Skip its
     "Report and stop": once the build is done, go on to validate.
   - **Validate**: announce `Autopilot · validate` and start its subagent
     with the fixed prompt, `<phase>` set to `validate`, and the validate
     line of `/specworks-done`:
     ```
     End with the report of step 4 of the skill before the Result line: PASS is Result: done, FAIL is Result: blocked.
     ```
     PASS or FAIL, the run stops there (step 4).

2. **Answer every stop by the rules**

   At every `Result: question` of a subagent, and at every point where
   build or done would ask the user (the API, a review finding, a new
   cycle), answer by these rules, in order:

   1. A question with options: take the option marked (recommended).
   2. A yes/no question that continues the flow is answered yes. It is one
      that agrees to the requirements or the API, or starts the next cycle.
   3. A question that needs free text, or has no option to take, stops autopilot.
   4. When the review of cycle 3 still has open findings, stop instead of starting cycle 4.

   Write each answer where the coordinators write it (the table above:
   design.md `## Interfaces`, the config, design.md or tasks.md, a
   finding's Decision with `specworks finding decide`), then append its
   entry to `autopilot.md` (step 3) before starting the next subagent.
   Never answer for a phase by doing its work, and never write an answer
   anywhere but where the question is about.

3. **Log every decision in `autopilot.md` when it is taken**

   A plain file in the change folder, written by this skill only; the
   phases commit it with the change folder. One entry per decision,
   appended when it is taken, never rewritten:
   ```
   # Autopilot: <ref>

   Started in <phase> on <date>.

   ## D<n> <phase>: <the question, one line>

   - **Options**: <the options as offered>
   - **Chosen**: <the option taken>
   - **Why**: <one line>
   - **Hard**: yes - <why> | no
   - **Undo**: <how to undo it> (hard ones only)

   ## Stop: <reason>
   ```

   A decision is hard when its options were close, when it settles product intent or an API, or when it is costly to undo.
   A second cycle and every later one is hard. `D<n>` counts on from the
   last entry, also in a resumed run. When the run stops, append the
   `## Stop:` line with its reason.

4. **Report and stop**

   Autopilot stops when validate passes; when a phase returns
   `Result: blocked` or validate fails; when a question needs free text or
   has no option to take; or when the review of cycle 3 still has open
   findings. Read the report from `autopilot.md`:

   ```
   Autopilot <ref>: stopped - validate passed

   Decisions to validate
     D2 design: the API of ResetService      hard: settles the API   undo: back to design
     D5 build: start cycle 2                 hard: a second cycle    undo: reopen review

   Also taken
     D1 specify: agree to the requirements -> yes
     D3 review: R1 code-gap -> back to code
   ```

   First the stop reason, then `Decisions to validate` (the hard ones,
   each with its undo), then `Also taken` (the rest, one line each). When
   validate passed, end with:
   ```
   1. /specworks-done <ref> (recommended): validate passed; close it once you agree with the decisions
   2. Stop here
   ```
   Otherwise offer the skill the stop points to (the phase a blocked or
   failed check goes back to, or the question autopilot could not answer,
   asked of the user as it is) as the recommended option, with `Stop here`.

---

## Guardrails

- Never run in refine, never run close, never push.
- Every phase follows its own skill, in its own subagent, with the fixed
  prompt: nothing from this conversation, only what is on disk.
- Every decision is in `autopilot.md` before the next subagent starts.
- Never skip a gate, weaken a test or mark a finding resolved to keep
  going; a blocked phase stops the run.
- After cycle 3, stop rather than start another cycle: repeated findings
  need the user, not another cycle.
