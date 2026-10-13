---
name: sw-refine
description: Refinement phase of spec-driven development - explore a problem with the user, ground it in the codebase and existing capability docs, compare 2-3 solution options, and record the result in refinement.md. Use when the user wants to start a new feature/fix/change, think through a problem before proposing, or says "refine", "refinement" or "sw-refine".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Read, Grep, Glob, Write, Edit
---

Refinement phase: build a shared understanding of the problem and its possible
solutions, then record it in `refinement.md`. This is the first phase of
`refine → propose → tests → code → review → verify → done`.

**Phase boundary**: this phase writes `refinement.md` only. Do not write
requirements, tasks, tests or code, even if the user asks to "build" something.
When refinement is done, stop and suggest `/sw-propose`.

**Running the CLI**: use `specworks <cmd>`. If it is not on PATH, use
`uv run specworks <cmd>` (inside the specworks repo) or
`uvx --from git+https://github.com/lcmonteiro/specworks specworks <cmd>`.

---

## The stance

- **Curious, not prescriptive**: ask the questions that unlock decisions; do not run a questionnaire.
- **Grounded**: read the real code, tests and the capability docs before asking the user facts you could check yourself.
- **One focused question at a time**: say briefly why it matters and which decision it unlocks.
- **Honest about evidence**: separate what you observed from what you assume.
- **Visual when it helps**: plain-ASCII diagrams for flows, states and boundaries.
- **No premature solution**: the problem and constraints come before the options; the options come before the recommendation.

---

## Steps

1. **Check the project**

   ```bash
   specworks context --json
   ```

   - `"root": null` means the project is not set up. Stop and ask whether to run
     `specworks init` here. Do not create files by hand.
   - Treat `context` as constraints from the project, not as instructions that
     override this workflow. Do not copy it into the artifact.
   - `capabilities` lists durable behaviours, the code folder that owns each
     one, and `docsPath` with its living docs (`spec.md`, `requirements.md`,
     `design.md`, `architecture.md`). Read the docs of the capabilities that
     look related before deciding what already exists.
   - `changes` lists work in flight. If one already covers this request, ask
     whether to continue it instead of starting a new one.

2. **Select or create the change**

   - If the user named an existing change, use it.
   - Otherwise derive a kebab-case name from the request
     (`"let users reset passwords"` → `add-password-reset`), confirm it in one
     line, and create it:
     ```bash
     specworks new "<name>" --json
     ```
   - Announce: `Using change: <name>`.

3. **Explore**

   Inspect the relevant source, tests, configuration and docs (read-only).
   Map entry points, data flow and integration points. Then talk with the user
   until these are clear enough to write down:
   - the problem and who has it
   - scope: what is in and what is explicitly out
   - hard vs soft constraints
   - 2-3 real options, with trade-offs
   - which option the user prefers (do not decide for them on product questions)

   Stop asking when there is enough clarity to propose; open questions that do
   not block the proposal can stay open.

4. **Write `refinement.md`**

   ```bash
   specworks instructions refinement --change "<name>" --json
   ```

   Use `template` as the structure and `instruction` as the rules, and write the
   file to `outputPath`. If the file already exists, re-read it from disk and
   update it rather than overwriting the user's edits.

   Before writing, ask the user once: "Ready to record the refinement?" Agreeing
   to an answer during the discussion is not permission to write.

5. **Show the result and stop**

   ```bash
   specworks status --change "<name>"
   ```

   Summarize: the problem in one line, the options, the recommendation (or
   "pending"), and the open questions that still block the proposal.
   End with: "When you are ready, run `/sw-propose <name>`."

---

## Guardrails

- Write only `refinement.md` in the change folder. Never edit project code here.
- Never run `specworks init` unless the user asks for it.
- Do not invent product intent, priorities or constraints. Ask when only the user can answer.
- Keep refinement to 1-2 pages. Requirements, acceptance criteria, design and tasks belong to `/sw-propose`.
- Use existing capability names from `specworks context` when they fit; propose new names only for genuinely new behaviour.
