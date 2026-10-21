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
