---
name: specworks-refine
description: Refinement phase of spec-driven development - explore a problem with the user, ground it in the codebase and existing capability docs, compare 2-3 solution options, and record the result in refinement.md. Use when the user wants to start a new feature/fix/change, think through a problem before proposing, or says "refine", "refinement" or "specworks refine".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Read, Grep, Glob, Write, Edit
---

Refinement phase: build a shared understanding of the problem and its possible
solutions, then record it in `refinement.md`. This is the first phase of
`refine → propose → test → implement → review → verify → close`.

**Phase boundary**: this phase writes `refinement.md` only. Do not write
requirements, tasks, tests or code, even if the user asks to "build" something.
When refinement is done, stop and suggest `/specworks-propose`.

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
     override this workflow. Do not copy it into the artifact. It is already
     merged top-level first, then each module down to the current one
     (`contextChain`): a module adds rules, it never removes its parent's.
   - `capabilities` lists durable behaviours of the WHOLE workspace, the code
     folder that owns each one, and `docsPath` with its living docs
     (`spec.md`, `requirements.md`, `design.md`, `architecture.md`).
     Capabilities of other modules are named `module:capability`
     (e.g. `billing:invoices`). Read the docs of the capabilities that look
     related, in any module, before deciding what already exists.
   - `module` is the module you are in (`(top)` for the top-level project) and
     `modules` lists every module. `missingModules` are listed by a parent but
     not checked out: say so if the request touches one.
   - `changes` lists work in flight in the current module (add `--all` for
     every module). If one already covers this request, ask whether to
     continue it instead of starting a new one.
   - Every path in the output is relative to `root`, the workspace root.

2. **Select or create the change**

   - If the user named an existing change, use it.
   - Otherwise derive a kebab-case name from the request
     (`"let users reset passwords"` → `add-password-reset`) and pick the
     module that owns it:
     - one module's behaviour only → that module;
     - several modules, or shared/cross-cutting behaviour → the top level
       (or the lowest module that contains all of them).
     Confirm name and module in one line, then create it:
     ```bash
     specworks new "<name>" --module "<module>" --json   # omit --module for the current one
     ```
   - Use the `ref` it returns (`module:name`, or just `name` at the top level)
     for every later command, and announce: `Using change: <ref>`.

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
   specworks instructions refinement --change "<ref>" --json
   ```

   Use `template` as the structure and `instruction` as the rules, and write the
   file to `outputPath`. If the file already exists, re-read it from disk and
   update it rather than overwriting the user's edits.

   Before writing, ask the user once: "Ready to record the refinement?" Agreeing
   to an answer during the discussion is not permission to write.

5. **Show the result and stop**

   ```bash
   specworks status --change "<ref>"
   ```

   Summarize: the problem in one line, the options, the recommendation (or
   "pending"), and the open questions that still block the proposal.
   End with: "When you are ready, run `/specworks-propose <ref>`."

---

## Guardrails

- Write only `refinement.md` in the change folder. Never edit project code here.
- Never run `specworks init` unless the user asks for it.
- Do not invent product intent, priorities or constraints. Ask when only the user can answer.
- Keep refinement to 1-2 pages. Requirements, acceptance criteria, design and tasks belong to `/specworks-propose`.
- Use existing capability names from `specworks context` when they fit, qualified with their module (`billing:invoices`); propose new names only for genuinely new behaviour, and say which module should own each one.
