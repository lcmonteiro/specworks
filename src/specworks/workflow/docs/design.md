# Design: workflow

## Overview

The workflow a change goes through,
`refine → specify → design → implement (test | code) → review → validate → close`, as far as
the CLI can check it. The phase skills do the work that needs judgement; this
capability gives them facts and gates.
- **Artifacts** (`artifacts.py`): the artifact graph from the packaged
  `schema.yaml` (what each phase writes and what it requires), each artifact's
  state, the instructions and template for writing it, and each half's task
  progress in implement.
- **Checks** (`checks.py`): every check defined once, as a function of a
  `GateContext` that computes what it reads (analysis, review report, review.md)
  on first use.
- **Gates** (`gate.py`): each phase's (and each half's) list of checks, and
  `start`, which runs the gates a phase depends on before moving the change.
- **Review** (`review.py`): the drift report (changed files against the base
  branch, untagged code and tests), the parser for review.md, and the writers
  that add findings and their follow-up lines to it.
- **Cycles** (`cycle.py`): which steps the next build cycle runs after a
  review.
- **Validate** (`validate.py`): the grouped, read-only final report.
- **Merge** (`merge.py`): merging a half's branch into the checkout in a
  build, resolving the change's `tasks.md` and `traceability.md`.

## Decisions

### Gates only check what the CLI can see

The gates look at specs, tasks, tags, review.md, git and the project's own
commands. Anything that needs judgement (whether a test fails for the right
reason, whether the code matches the spec's intent) stays with the skills.
(baseline-workflow)

### A change's interfaces live in its own module

The design gate counts a file named under Interfaces only when it exists inside
the change's module folder. The path may be written relative to the module or
to the workspace root, the form every CLI path is printed in. A same-named file
elsewhere in the workspace must not stand in for a missing stub, and work
across modules belongs to a change at the top level or in the lowest common
module. (module-interface-paths)

### One definition per check, shared by gates and validate

Gates and validate are lists of the same check functions. Validate adds a
group and the phase skill that fixes each failure, and `start` prints that fix
too. A check returns `None` when it doesn't apply. Warnings
(`blocking=False`) never fail a gate. (baseline-workflow)

### Implement's halves are gated separately

`implement` has two halves that run in parallel, each reading only the
project, refinement, specs and design: the test half and the code half.
`gate test` and `gate code` each check one half (its `[test]` or `[code]`
tasks); `gate implement` runs the test gate, then the code gate once the test
gate passes, with each check named `test: ` or `code: `. `start` treats
implement's gate as both, so leaving implement needs both halves; going back
to implement needs only the design gate. The half checks are new functions
(`half_tasks_done`, `code_tests_pass`, `review_tests_pass`) rather than
parameters on `tests_pass`, so validate keeps its blocking-suite check
unchanged. (parallel-test-code) The code gate's `code_tests_pass` was later
removed, see below. (code-half-no-tests)

### Validate reports open tasks by kind

Validate has three task checks instead of one "every task is done": the
`[test]` and `[code]` halves' own `half_tasks_done(half)` checks (naming
`/specworks-test` and `/specworks-code`) and `unmarked_tasks_done` for tasks
with neither marker, design's stub tasks (naming `/specworks-design`). Each
check still names one skill, so a failure points to the phase that fixes it
and `goBackTo` keeps its shape. The unmarked check is its own function rather
than `half_tasks_done("")`, whose name is built from the marker and which the
gates never need. Open tasks of a change written before the markers existed
go to `/specworks-design`. With tasks.md missing all three fail, behind
`planning artifacts exist` naming `/specworks-specify`. The single
`tasks_done` check is gone. (fix-validate-test-task-skill)

### The code gate does not run the tests

The code half is written without reading the change's tests, which the test
half writes in parallel and which are missing or red by design, so the code
gate needs no `@ac` test per criterion (parallel-test-code) and does not run
`commands.test` at all. It runs one check per configured command, `build`,
`typecheck` and `lint` in that order, each blocking when it fails and skipped
(`None`) when not configured, as `stubs_build` does for the design gate.
With none of the three configured, a `[warn]` check (`ok` False, `blocking`
False) says the tests run in review, and the gate passes. One combined check
was rejected (one failure would hide the others' output), and so was
`optional_command` (an "ok, not configured" line per missing command). So
`gate implement` and `start review` run no suite; the tests first meet the
code in review, whose gate runs the whole suite and blocks on it, except as a
warning under `--allow-open` while review.md has an open finding. A broken
existing test is no longer caught before review. (code-half-no-tests)

### A change's own tests include its changed test files

The design gate's `existing_tests_pass` reads one rule, `own_tests(ctx)`: the change has
tests of its own when it has `@ac` tests tagged with its criteria, or test
files changed since it started (kind `test` in `ctx.report.changed`, deleted
ones excluded). It returns the reason, which the warning names. Without the
second half, a change with no criteria of its own (skip-specs) got stuck in
implement when its halves disagreed (the code gate used it too until it
stopped running the suite). The changed files come from the same
diff `specworks review` computes, so the gates and review agree on what
changed; a second, lighter `git diff` in the gates was rejected. Without git
none are known and the suite blocks. The rule is read only for a red suite,
so a green one costs no diff. Test edits unrelated to the change also relax
the gate; that is accepted, since the review gate still blocks on the
whole suite. (fix-no-own-tests-gate)

### Specs are fingerprinted when they are agreed

Leaving specify through `start` records a fingerprint of each requirement.
Later gates warn, without blocking, when the specs drift from that agreement,
and starting design again accepts the new specs. (baseline-workflow)

### Deleted code is reviewed like changed code

The drift report lists files deleted on the branch (kind `deleted`, with the
kind they had). Deleted source and test files must be accounted for in
review.md, like untagged changed files, because the trace only checks the
change's own requirements: a deletion is where another requirement can silently
lose its code. Detecting that loss automatically (reading the deleted file's
tags at the base) was left for later. (review-deleted-files)

### review.md is parsed strictly

A checkbox the parser can't read, or an open finding with no known type or
`back to <step>:`, fails the review gate and validate, even inside a build.
A finding the parser misses would otherwise let a gate pass with it still open.
The same goes for any checkbox outside a finding, at the top level or indented
under another bullet: only sub-steps inside a finding's block are allowed, so
open work can't hide behind indentation. (baseline-workflow, review-indented-checkboxes)

### review.md is written by commands that read their edit back

The `finding` writers (`add_finding`, `decide_finding`, `mark_finding_done`,
`close_finding`) edit review.md's text in place: each finds the finding's
block as `parse_review` sees it (its checkbox line and the indented lines
after it), adds one line at the end of the block, replaces the Decision line
or ticks the box, then parses the new text and checks that the finding reads
back as expected (ID, state, step). Only then is the file written; otherwise a
`FindingError` names the problem and review.md is left as it was. The writers
use the reader's own rules (`FINDING_RE`, `TYPE_PHASE`, `BACK_RE`, `DONE_RE`,
`FINDING_STEPS`), so they cannot write what the gate would refuse. A
structured data file with review.md generated from it was rejected.
(finding-commands)
- A decision starts `back to <step>:`, `back to design only:` or
  `accepted:`; `accepted` ticks the box. `only` after any other step is
  refused before any write (`DECISION_FORM` names the three forms).
  (skip-halves-for-design-text) A new finding is expected to route where the reader routes it: the last
  `back to <step>:` in its text or proposal, else its type's step, so a
  proposal written in that form is not refused.
- With an ID repeated, the writers act on the first block with it, as
  `parse_review` does, and a refusal is a `FindingError`, never a traceback.
- `close_finding` adds `confirmed in review: <text>`; the parser does not
  route on it (only the box counts).
- A new review.md gets the template's title, `Base:` line, headings and
  comments, without its example lines, which would read as a bad finding.
- Replacing a Decision replaces its first line only: a hand-wrapped Decision
  keeps its continuation lines, and when they would misroute the finding the
  read-back refuses. Accepted, since the commands write one-line Decisions.

### Build cycles run only the steps the findings need

A finding's route is a step: `specify, design, implement, test, code,
review`. It is set by its type, by `back to <step>:` (`implement` means both
halves), or past a `done in <step>:` (specify → design, design → implement,
implement, test or code → review). `next_cycle` keeps its keys; its `phases`
lists the steps to run: code half and review, test half and review, both
halves and review, or design, both halves and review. A spec finding hands
over to specify instead of starting a cycle. Re-running every phase after the
earliest finding was replaced: a code finding no longer re-runs the tests.
(baseline-workflow, parallel-test-code)
- `back to design only:` sets the finding's `design_only`: once
  `done in design:`, it goes to review instead of implement, and it adds no
  half to the cycle. The halves join design only when a finding needs design
  without `only`, needs implement, or names that half: only design-only
  findings give `design, review`; design-only plus a code finding gives
  `design, code, review`. It is agreed in the Decision, before the cycle
  starts; detecting a text-only design change from git, or deciding it after
  the design step, were rejected. `only` reads with the `back to` that carries
  it, and the last route in the block wins, so a later plain `back to design:`
  clears it. (skip-halves-for-design-text)
- A route is read from any line of a finding's block, so a follow-up line
  that quotes a route form routes the finding too. Accepted as specified; it
  predates the design-only form. (skip-halves-for-design-text)

### Merging a half's branch resolves only tasks.md and the trace

Both implement halves tick `tasks.md` and rewrite `traceability.md`, so the
test half's worktree branch conflicts there on every build. `merge_branch`
refuses a dirty checkout or an unknown branch, runs `git merge --no-ff
--no-edit`, and on conflicts resolves only those two files of the change:
`tasks.md` keeps a line ticked when either side ticked it (`merge_ticks`,
reading both sides from the index), and the trace is regenerated for the
merged checkout. Any other conflicting file, or a `tasks.md` line that
differs in more than its box, runs `git merge --abort`, so the checkout is
never left half-merged. git's `union` strategy was rejected: it keeps both
versions of a line, so a task would appear twice. Two task files and a git
merge driver were rejected too. The merge commit keeps git's default message.
Its error, `BranchMergeError`, is named apart from `specs.merge.MergeError`,
which close raises. (merge-halves-without-conflicts)

## Interfaces

- `src/specworks/workflow/artifacts.py`: `load_artifacts()`,
  `artifact_states(change)`, `instructions(ws, module, change, artifact_id)`,
  `half_progress(change)` (`{"test": {"done", "total"}, "code": {...}}` in
  implement, else None; `status` shows it as `test 3/3, code 1/4`).
- `src/specworks/workflow/checks.py`: `Check`, `GateContext`, `passed(checks)`,
  `run_checks(ctx, checks)`, and the check functions (including
  `half_tasks_done(half)`, `unmarked_tasks_done`, `review_tests_pass`,
  `code_command(key, name) -> CheckFn` (runs `commands.<key>`, blocking on
  failure, `None` when not configured), `no_code_commands(ctx)` (the `[warn]`
  named `build, typecheck and lint` when none is configured)), and
  `own_tests(ctx) -> str | None` (why the change has tests of its own, or
  None; used by the design gate's `existing_tests_pass`).
- `src/specworks/workflow/gate.py`: `GATE_CHECKS` (`code`: specs, code tasks, tags,
  then `code_command` for build, typecheck and lint, then
  `no_code_commands`), `GATES` (with `test`, `code` and `implement`), `run_gate(ctx, phase)`, `gates_to_start(current, phase)`,
  `start_phase(ctx, phase)`.
- `src/specworks/workflow/review.py`: `review_change(analysis, base)`,
  `changed_paths(ws, since)`, `deleted_paths(ws, since)`, `ChangedFile` (`kind`, `was`),
  `ReviewReport`, `parse_review(text)`, `read_review(change)`, `ReviewDoc`,
  `Finding` (`phase` holds its step; `design_only`, shown as
  `"designOnly": true` by `to_dict()` when set), `FINDING_STEPS`; the writers, each
  returning the finding as `read_review` reads it after the write and raising
  `FindingError` with review.md unchanged:
  `add_finding(change, kind, text, proposal) -> Finding` (`kind` one of
  `TYPE_PHASE`; the next free ID, under `## Findings`),
  `decide_finding(change, finding_id, decision)`,
  `mark_finding_done(change, finding_id, step, text)` (`step` one of specify,
  design, implement, test, code), `close_finding(change, finding_id, text)`.
  Lines written: `  - **Proposal**: …`, `  - **Decision**: …`,
  `  - done in <step>: …`, `  - confirmed in review: …`.
- `src/specworks/workflow/cycle.py`: `next_cycle(change)` (`reviewed`, `open`,
  `startAt`, `phases`, `handOver`; `phases` lists steps).
- `src/specworks/workflow/validate.py`: `VALIDATE` (rows of group, the skill
  that fixes a failure, check), `validate_change(ctx)`, `summary(checks)`.
- `src/specworks/workflow/merge.py`: `merge_branch(ws, module, change, branch)
  -> MergeResult` (raises `BranchMergeError`, and `GitError` outside a git
  repository), `MergeResult(merged, branch, resolved)` (`merged` is False only
  when there was nothing to merge; `to_dict(ws)` gives workspace-relative
  paths), `BranchMergeError` (`files`: the conflicting files, empty when
  refused before merging), `merge_ticks(ours, theirs) -> str | None` (None
  when a line differs in more than its box).

## Constraints

- Validate and the gates write nothing to the project. Only `start` writes, to
  the change's metadata, `merge_branch`, which commits a merge or leaves
  the checkout as it was, and the finding writers, which write only the
  change's review.md and only when it reads back as expected.
- Built on `project` (config, workspace, changes, runner) and `specs` (specs,
  tags, trace).
