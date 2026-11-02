---
name: specworks-onboard
description: Get started with specworks - say where the project stands and the one skill to run next (from the installed CLI), explain the basic loop (refine → specify → build → done, its gates and the ways back), and answer questions about specworks and the project, read-only. Use the first time someone uses specworks in a project, when they are getting started, lost or unsure what to run next, ask how specworks works, or say "onboard", "where am I" or "specworks onboard".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Read, Grep, Glob
---

Onboard: the entry point for someone new to specworks. It says where their
project stands and which skill comes next, explains the basic loop, and
answers their questions, grounded in the installed CLI and their real
project. It does no phase's work: it points to the skill that does.

It sits beside the flow `refine → specify → design → implement (test | code) → review → validate → close`,
not in it.

**Phase boundary**: This skill never changes files. It runs only the CLI's
read commands: `specworks context --json`, `specworks list`,
`specworks status --change "<ref>"`, `specworks gate <phase> --change "<ref>"`,
`specworks check --change "<ref>"`, `specworks trace --change "<ref>"`,
`specworks spec list`, `specworks spec show <capability>`,
`specworks spec find <terms>`, and `--help` on any command. Every command
that writes (`init`, `update`, `skills`, `new`, `start`, `phase`, `commit`,
`close`, `config set`, ...) is given to the user to run, or left to the skill
that owns it, never run here.

<!-- specworks:include running-cli -->

<!-- specworks:include asking-the-user -->

---

## Steps

1. **Where the project stands**

   ```bash
   specworks context --json
   ```

   Go down the table; the first row that matches decides the recommended
   next step:

   | What the CLI shows | State | Next |
   |---|---|---|
   | `"root": null` (or `specworks` is not installed) | not a specworks project | install with `uv tool install git+https://github.com/lcmonteiro/specworks`, run `specworks init`, then `/specworks-start` (no code yet) or `/specworks-adopt` (existing code); give these, do not run them |
   | `skills.state` is not `current` | skills out of date | `specworks update` |
   | `capabilities` is empty | set up, nothing mapped | `/specworks-start` when the repository has no code, `/specworks-adopt` when it has |
   | a capability with `"hasSpec": false` | not baselined | `/specworks-baseline <capability>` |
   | `changes` is not empty | work in flight | per change, from its phase (below) |
   | otherwise | ready | `/specworks-refine <what you want>` |

   For each change in flight, from its `phase` (run
   `specworks status --change "<ref>"`, and `specworks gate <phase> --change "<ref>"`
   when it matters):
   - `refine`: `/specworks-specify <ref>` when `refinement.md` is done,
     else `/specworks-refine <ref>`;
   - `specify`: `/specworks-specify <ref>` until `gate specify` passes, then
     `/specworks-build <ref>`;
   - `design`, `implement`, `review`: `/specworks-build <ref>`;
   - `validate`, `close`: `/specworks-done <ref>`.

   A baseline change (`baseline-<capability>`, from `/specworks-adopt`) runs
   its own design, implement and review inside `/specworks-baseline`, so it
   does not follow the list above:
   - in `specify`, `design` or `implement`, or in `review` before
     `gate review` passes: `/specworks-baseline <capability>`;
   - in `review` once `gate review` passes, and in `validate` or `close`:
     `/specworks-done baseline-<capability>`.

   Several rows can apply at once (skills out of date and changes in
   flight): report each one, in table order, and recommend the first. To
   tell whether a repository has code, look at its files (Glob), not at the
   config. Say the state in one line, e.g. `State: set up, no capabilities
   mapped yet (existing code found in src/)`, then the next step and why.

   If the user only wanted to know where they are, stop here with the next
   step as the closing question, e.g.:
   ```
   1. /specworks-adopt (recommended): the repository already has code to map
   2. Explain the basic loop first
   3. Stop here
   ```

2. **The basic loop (the primer)**

   When the user asks how specworks works, or is new to it, explain from
   this primer, briefly, and only the parts they need. Check anything
   concrete against the CLI (step 3).

   - **The flow**: `refine → specify → build → done`. `/specworks-build`
     runs `design → implement (test | code) → review` in cycles, and
     `/specworks-done` runs `validate → close`. A project starts with
     `/specworks-start` (no code) or `/specworks-adopt` (existing code, then
     `/specworks-baseline` per capability).
   - **What each step writes** (in `.specworks/changes/active/<change>/`):
     - refine: `refinement.md` (problem, options, recommendation);
     - specify: `proposal.md`, delta specs (requirements and acceptance
       criteria), `design.md`, `tasks.md`, `traceability.md`;
     - design: the API under Interfaces in `design.md`, as stubs that build;
     - implement: failing tests tagged `@ac` (test half) and the real code
       tagged `@req` (code half), independently;
     - review: `review.md`, every drift between code, spec and design, and
       its decision;
     - validate: a read-only PASS/FAIL report;
     - close: the specs merged into the living docs, the change archived.
   - **Capabilities and living docs**: a capability is a durable behaviour
     owned by a code folder. Its living docs (`spec.md`, `requirements.md`,
     `design.md`) are in `<path>/docs/`, written only by `specworks close`.
   - **IDs and tags**: each requirement has an ID (`REQ-<PREFIX>-001`) and
     each acceptance criterion one under it (`AC-<PREFIX>-001.1`). Tests
     carry `@ac AC-…`, code carries `@req REQ-…`; `specworks trace` shows
     the matrix. IDs are never renumbered or reused.
   - **Gates**: a phase ends only when `specworks gate <phase>` passes;
     `specworks start <phase>` runs the gates left behind before it moves
     the change.
   - **The ways back**: review records each finding with the phase that owns
     it (specify, design, test, code), and the build runs a new cycle for
     them; each failed validate check names the skill that fixes it.
   - **Depth**: the wiki, https://github.com/lcmonteiro/specworks/wiki:
     Concepts, Tutorial, Skills, CLI, Reference.

3. **Answer questions**

   Answer from these sources, in this order, and say which one you used:
   1. The user's project and the installed CLI: `specworks context --json`,
      `specworks status --change "<ref>"`, `specworks gate <phase> --change "<ref>"`,
      `specworks check --change "<ref>"`, `specworks trace --change "<ref>"`,
      `specworks spec list`, `specworks spec show <capability>`,
      `specworks spec find <terms>`, and `--help` on any command.
   2. The primer (step 2).
   3. An installed skill's own `SKILL.md` (next to this skill,
      `../specworks-<name>/SKILL.md`), for what a skill does step by step.
   4. A wiki page for depth, as a link under
      https://github.com/lcmonteiro/specworks/wiki; do not fetch it.

   When the CLI and the primer disagree, the CLI wins: say so, and answer
   from the CLI. When none of the sources answers, say so instead of
   guessing.

   For "why did this gate fail?": run the gate, name each failing check and
   the skill that fixes it; do not fix it.

   End every answer with the closing question: the next step from step 1
   (recommended), another question, or `stop here`.

---

## Guardrails

- Read-only: never write, edit or delete a file, and never run a command
  that writes (see the phase boundary). Give the command or the
  skill instead.
- Recommend one next step at a time, from the CLI's output, not from
  memory.
- Keep the primer short; link the wiki for depth instead of copying it.
- Never do a phase's work here, even a small one: hand over to its skill.
