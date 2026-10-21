---
name: specworks-close
description: Close phase of spec-driven development - fold a verified change into the project's living documentation next to the code (spec, requirements index, design, architecture, diagrams), register new capabilities, and archive the change. Use when a specworks change has passed validate and the user wants to finish it, or says "close the change", "archive the change", "merge the specs" or "specworks close".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Read, Grep, Glob, Write, Edit
---

Close phase: turn what the change decided into the project's lasting truth.
The deltas are merged into each capability's living docs next to its code,
the design knowledge worth keeping moves there too, and the change folder is
archived as the record of how it happened.

It is the last phase of `refine → specify → design → implement (test | code) → review → validate → close`.

**Phase boundary**: edit only the living docs (`<capability path>/<docs_dir>/`)
and, for new capabilities, the config. No code, tests or delta specs change
here; if something is wrong, go back to the phase that owns it.

<!-- specworks:include running-cli -->

<!-- specworks:include asking-the-user -->

<!-- specworks:include picking-the-change -->

---

## Steps

1. **Pick the change and start the phase once it passes validate**

   Pick the change (above), then:
   ```bash
   specworks start close --change "<ref>"
   ```

   It runs `gate validate` (the same checks as `specworks validate`) and moves
   the change to close only if it passes. If it fails, stop and point to the
   phase each failed check names (`-> /specworks-<phase>`; `/specworks-validate`
   explains them). `specworks close` refuses a change that does not pass.

   The gate cannot see what `/specworks-validate` found by reading (step 3).
   If validate reported FAIL for this change in this conversation, its
   reading included, and nothing changed since, stop as well: closing it
   anyway would make `/specworks-validate` + `/specworks-close` close what
   `/specworks-done` refuses.

2. **Register new capabilities**

   For every capability under "New Capabilities" in proposal.md (or any delta
   whose `specworks spec show <ref> --json` says `"new": true`), ask "Register
   `<name>` in `<module>` at `<code path>`? (yes/no)" (on no, take the
   user's module and path), then:
   ```bash
   specworks capability add <name> --path <code path> [--module <module>] [--prefix <P>] [--description "<one line>"]
   ```
   Keep the prefix the delta's IDs already use (`spec show` gives it), or
   the IDs no longer match.

3. **Show the merge plan and get a go-ahead**

   ```bash
   specworks close --change "<ref>" --dry-run --no-run
   ```

   `--no-run` skips the test, lint and typecheck commands: step 1 just ran
   them and nothing but the config changed since. Step 5 runs them again
   before anything is written.

   Show, per capability: the living spec it writes (new or existing) and the
   requirements added, modified and removed. Ask: "Merge and archive? (yes/no)"
   Nothing is written until the user agrees.

4. **Update the living design and architecture (before archiving)**

   The change folder moves in the next step, so do this first. For each
   capability the change touched, in its docs folder (`docsPath` from
   `specworks context --json`):
   - **design.md**: the lasting design of the capability as it is now, not the
     story of this change: Overview, Decisions (each with why, alternatives,
     and the change that introduced it: `(add-password-reset)`), Interfaces
     (public APIs, data shapes, events), Constraints. Fold in the decisions
     from the change's design.md that still hold; drop the ones review.md
     overturned; leave out task-level detail.
   - **architecture.md**: only when the change altered structure: components
     and their responsibilities, dependencies between modules and services,
     data flows, deployment units.
   - **diagrams**: copy the change's diagrams that describe the system as it
     now is into `<docsPath>/diagrams/` (the `.d2` source; update it if
     review changed the design), render them and embed them:
     ```bash
     specworks diagrams --dir "<docsPath>"
     ```
   Create the files if they do not exist yet. Keep them short and current;
   they are what the next refinement reads.

5. **Merge and archive**

   ```bash
   specworks close --change "<ref>"
   ```

   This applies every delta to `spec.md` (ADDED appended, MODIFIED replaced in
   place by ID, REMOVED deleted, everything else kept), regenerates
   `requirements.md` (index of requirements and criteria, plus a History line
   for this change), sets the phase to `done` and moves the change to
   `<dir>/changes/archive/<date>-<name>/`.

6. **Report and stop**

   Summarize: living docs written per capability (spec, requirements, design,
   architecture, diagrams), requirements added / modified / removed,
   capabilities registered, and the archive path. Suggest committing the
   living docs, the archive and the code together, e.g.
   `git add -A && git commit -m "<change>: close"`, and opening the PR if the
   project uses them.

   When the change was a baseline (`baseline-<capability>`), name what is
   next: the next capability with 0 requirements in `specworks spec list`
   (`/specworks-baseline <capability>`), or, when none is left, that every
   capability now has a living spec and new work starts with
   `/specworks-refine` (the waiting `fix-*` changes of suspected bugs first).

   End with the next steps as numbered options, for example:
   ```
   1. Commit and open a PR (recommended): the living docs, the archive and the code go together
   2. /specworks-baseline <next capability>: after a baseline, when one is left
   3. Stop here
   ```
   (after the last baseline: `/specworks-refine <fix-ref>` for the first
   waiting bug change instead of option 2).

---

## Guardrails

- Never close a change that does not pass `specworks validate`.
- Do not edit spec.md or requirements.md by hand; they are produced by
  `specworks close` from the deltas. Change requirements through a new change.
- Living docs describe the system as it is now. History belongs in the
  archive and in requirements.md's History, not in design.md prose.
- Ask before merging (step 3) and before registering a capability (step 2).
