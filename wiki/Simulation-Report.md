# Simulation report: a messy multi-feature project

A sandbox Python project (`todo`, git, pytest) was driven through the specworks
CLI the way a hurried person (or agent) would: features opened before others
closed, specs changed mid-build, IDs copy-pasted, phases jumped with `phase`,
work done on `main`, uncommitted closes, hand-edited living docs.

Changes run: `add-due-dates`, `add-priorities` (opened while the first was in
design), `sort-overdue` (abandoned), `replace-due-with-deadline` (REMOVED a
requirement), `cli-add-command` (cross-module, module `cli`), `search-items`,
plus throwaway ones to probe edge cases. The repo's suite was green throughout
(387 passed).

## What worked well

- Clear, actionable errors: kebab-case names, `###` vs `####` scenarios,
  missing SHALL/MUST, missing **Migration**, unknown task numbers, `phase done`
  refused, missing interface files, unconfigured `commands.test`.
- Cross-change ID protection: the same ID ADDED twice, one requirement
  MODIFIED by two changes, re-adding a removed or existing ID.
- `spec show` takes in-flight changes into account for `nextId`.
- Removed requirements still tagged in tests fail `gate code`.
- `close` is atomic: the archive target is checked before anything is written.
- Modules and cross-module changes (`specs/cli/commands/spec.md`) work end to end.
- `cycle` routes findings correctly, including `done in <phase>`.

## Problems found

Ranked by how much they hurt. **Bug** means wrong behaviour, **Gap** means a
mistake goes unnoticed, **UX** means confusing output.

### High

1. **Bug: deadlock between two changes MODIFYing one requirement.** *(Fixed.)* Both
   changes become INVALID, so neither can pass validate and neither can close.
   The advice ("close one change first") can't be followed. The only way out
   is to edit one change by hand.
2. **Bug: one change's tags break another change.** *(Fixed.)* With two active changes
   on one capability, change B's valid `@ac AC-…-003.1` counts as an *unknown
   tag* for change A, so A's `gate test` and `gate code` fail. Parallel work
   on one capability is blocked.
3. **Bug: an ID clash is reported to both changes the same way.** *(Fixed.)* When a new
   change reuses an ID, the older change (already in design, the first to use
   the ID) also becomes INVALID and is told to "take the next free ID". Its
   gates fail because of the newer change's mistake.
4. **Gap: typos in the tag prefix are never reported.** *(Fixed.)* `@ac AC-TODO-ITEM-002.1`
   (missing `S`) passes "no tag refers to an unknown requirement".
   `unknown_tags` only looks at IDs whose prefix belongs to the change's own
   capabilities.
5. **Gap: working on the base branch hides the change's commits.** *(Fixed.)* On `main`
   the merge base is `HEAD`, so review only sees uncommitted files. An
   untagged, never-implemented stub (`src/todo/dates.py`) passed review and
   validate, with no warning.
6. **Gap: a broken living spec is never checked.** *(Fixed.)* A hand-edited `spec.md`
   with a duplicate `REQ-…-003` and a requirement with no ID passes every
   command. `spec show` prints `None` as the ID, and `close` writes both into
   `requirements.md`.
7. **Gap: the run cache can show a red suite as green.** *(Fixed.)* After a git-ignored
   `.env` broke the suite, `gate design` reused the old green result. This is
   documented, but gate, start and validate have no `--fresh` flag.

### Medium

8. **Gap: a capability that was never registered is only reported at
   `close`.** *(Fixed.)* Every earlier command passes.
9. **Gap: `capability add --prefix TODO` broke every in-flight ID silently.**
   It invalidated the IDs of two active changes without a warning, and there
   is no command to edit a capability's prefix or rename the capability.
10. **Gap: editing the spec after specify goes unnoticed.** *(Fixed.)* Wording changed
    (`<` to `<=`) and an AC was renumbered during design. All tasks stayed
    ticked, and code that no longer matches the wording passed `gate code`.
11. **Gap: a MODIFIED requirement needs no new test.** *(Fixed.)* If its AC IDs stay
    the same, the old tests satisfy "every AC has a test", so a behaviour
    change can ship untested.
12. **Gap: the test gate never runs the tests.** A test that can't fail
    (`assert … or True`) counts as the "failing test" for its AC.
13. **Gap: a stale `traceability.md` passes validate.** One still showing
    "no tests, no code" was archived as the change's evidence.
14. **Bug: a zombie change after an uncommitted close.** *(Fixed.)* I closed without
    committing and then switched branches. Git restored a partial copy of the
    change (no `proposal.md`, phase `code`) next to its archived copy, and
    `list` showed it as active.
15. **Gap: phase order isn't enforced at close.** A change in `specify` (with
    skip-specs) passed validate and reached close. "Went through review" is
    only a warning.
16. **Gap: no way to abandon or park a change.** *(Fixed.)* The only way is `rm -rf`.
    Archived changes can't be opened by any command either (`status` says
    "not found").

### Low

17. **Gap: `tasks.md` accepts `- []` and `- [~]` silently.** A task with no
    IDs isn't flagged, even though the rules say every task names its IDs.
18. **Gap: the proposal's Capabilities list isn't checked against the delta
    specs.** A listed `todo-prio` with no delta and no capability went
    unnoticed.
19. **Gap: problems in `review.md` go unflagged.** Two findings with the same
    ID (two `R1`) aren't reported, and an open sub-checkbox under a resolved
    finding is ignored. `cycle` routes an unknown type (`perf -> code`, exit 0)
    that `gate review` calls unreadable.
20. **UX: validate shows `[ok] lint passes` and `[ok] typecheck passes` when
    neither is configured.** The "not configured" detail is hidden.
21. **UX: a delta at `specs/commands/` instead of `specs/cli/commands/` silently
    becomes a new top-level capability.** The error talks about the prefix,
    not the path.
22. **UX: `new <name>` accepts the name of an archived change.** *(Fixed.)* Closing it on
    the same day then fails at the very end, with an absolute path in the error.
23. **UX: other small problems.**
    - A delta's `## Purpose` on an existing capability is dropped silently.
    - The dropped-AC warning can't be marked as intended, so it repeats on
      every gate.
    - `new archive` says "already exists" instead of "reserved name". *(Fixed.)*
    - The error for an unconfigured `lint` suggests `e.g. test: uv run pytest`.
    - Branch-wide changed files make each change account for another change's
      files.
24. **Docs: the walkthrough no longer matches the CLI.**
    - It says `spec.yml` gets the test command, but `init` leaves `test:` empty
      (the walkthrough test fills it in itself).
    - Its `gate specify` output shows "every acceptance criterion has a task",
      which the gate no longer prints (`docs/walkthrough.md:81`).

## Fixed since

Items 1–4 are fixed:

- A clash between two active changes (the same ID ADDED, or one requirement
  MODIFIED/REMOVED by both) is an error only in the change that started later,
  and a warning in the earlier one, which can still close. New changes record
  when they started (`created: 'YYYY-MM-DDTHH:MM:SS'`). Changes that only have
  a date sort first that day, then by name.
- IDs in another active change's delta specs are known tags.
- A tag whose prefix no capability uses (registered, or new in an active
  change) is unknown for every change, with a "did you mean". So is a tag that
  is not a REQ/AC ID at all.

Items 5–7 are fixed:

- On the base branch, review compares with the commit before the change
  started (the parent of the newest commit that added its `.change.yaml`).
  When no commit marks that, `gate review` and `validate` warn that only
  uncommitted files are compared.
- `check` warns about problems in the living spec of each capability a change
  touches: an ID used twice, a requirement or criterion without an ID, no
  scenario, or no SHALL/MUST. `close` refuses to merge into a broken one.
  `spec show` prints `(no ID)` instead of `None`.
- `gate`, `start` and `validate` take `--fresh`. It runs each project command
  for real once per invocation, however many gates use it.

Items 8, 14, 16 and 22 are fixed:

- `check` warns about a new capability that is not registered yet, from the
  specify phase on, with the exact `capability add` command.
- `specworks abandon --change <ref> --reason <why>` archives a change without
  merging. `list --archived` lists closed and abandoned changes, and `status`
  reads an archived one. Other commands say a change is archived instead of
  "not found".
- `new` refuses `archive` and the name of an archived change. The "already
  exists in the archive" error no longer shows an absolute path.
- `list` and `check` flag an active change that is also archived: the leftover
  copy a branch switch restores after an uncommitted close.

Items 10 and 11 are fixed:

- When `start` passes the specify gate, it records a fingerprint of each
  requirement. Later gates and validate warn about every requirement changed,
  added or dropped since then, and `start design` accepts the new specs.
- Review and validate warn about a MODIFIED requirement whose behaviour
  changes while none of its test files changed on the branch.

Both are warnings, not blocks: the task boxes stay as they are, for the agent
to untick once warned.

## Suggested fixes and improvements

**Concurrency between changes (1–3, 22)**

- Report a clash only on the change created later (by `created`, then by
  name). The older change gets a warning. This removes both the deadlock and
  the case where a new change breaks an old one.
- Count the IDs of other active changes as known (`known_ids` across
  `list_changes`). Report a tag as "belongs to change X" in a warning, not as
  unknown.
- `new` should refuse names already in the archive and the reserved name
  `archive`.

**Tag and ID hygiene (4, 6, 9)**

- Report any tag whose prefix matches no capability in the workspace
  ("unknown prefix TODO-ITEM; did you mean TODO-ITEMS?").
- Add `specworks spec lint` (and run it in `check`/`validate` for the touched
  capabilities). It should flag duplicate IDs, requirements with no ID or no
  scenario, and missing SHALL/MUST in living specs. `close` should refuse to
  merge into an invalid living spec.
- Before saving, `capability add` should check active changes for IDs that the
  new prefix would invalidate. Add `capability set <name> --prefix/--path`.

**Review and base detection (5, 13, 23)**

- When `HEAD` equals the base, or the merge base is `HEAD`, warn: "on the base
  branch: committed work of this change is invisible; pass --base". A fallback
  base could be the commit where the change folder first appeared
  (`git log --diff-filter=A -- <change>/.change.yaml`).
- `validate` should compare `traceability.md` with a fresh `to_markdown` and
  warn when it differs (or regenerate it on close).

**Drift after planning (10–12)**

- Save a hash of the delta specs when `gate specify` passes, in
  `.change.yaml`. Later gates warn "specs changed since specify; re-run
  `start specify`" and could untick the affected tasks.
- For MODIFIED requirements, ask for at least one test that changed in the
  diff, or warn "REQ-… is MODIFIED but none of its tests changed".
- `gate test` could optionally run the tests and check that each new `@ac`
  test fails (`--expect-red`).

**Lifecycle (14–16, 8)**

- Add `specworks abandon <ref>` (archive with status `abandoned`, no merge),
  plus `list --archived` and `status` on archived refs.
- `list` and `check` should warn when an active change has the same name as an
  archived one, or has no `proposal.md`. After `close`, print a hint to commit.
- `close` should require phase `validate` (with `--force` to skip).
- From specify on, warn about new capabilities that aren't registered, with
  the exact `capability add` command.

**Smaller items (7, 17–21, 23)**

- Add `--fresh` to `gate`, `start` and `validate` (same effect as
  `SPECWORKS_RUN_CACHE=0`).
- Make the checkbox mark strict (` `, `x`, `X`). Warn on tasks with no IDs.
- Check that every capability in the proposal has a delta spec, and the
  reverse.
- In `review.md`, report duplicate finding IDs and open nested checkboxes.
  Make `cycle` fail on findings that can't be read.
- Show unconfigured optional commands as `[skip]` in validate.
- When a delta's folder name matches a capability in a module, suggest the
  right path.
- Warn when a delta's `## Purpose` will be ignored. Allow
  `<!-- specworks: drops AC-… on purpose -->` to silence the dropped-AC
  warning.
- Fix the example in the "not configured" error.
- Update the walkthrough's set-up text and gate-specify output.
