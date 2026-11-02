# Refinement: specify-related-requirements

## Problem

Specify writes a delta for the new behaviour but has no step that finds the
existing living requirements about the same command, flag or config key, so
they stay unchanged and contradict the delta. Review catches it later and
each one costs a cycle back to specify: in add-branch-default, three of four
findings (REQ-CLI-006 twice, REQ-CLI-013) were older requirements on `new`
and `config set` that the delta did not modify.

## Outcomes

- Before writing the delta specs, specify lists every living requirement
  that mentions what the change touches (its commands, flags, config keys),
  across all capabilities.
- For each one, specify modifies it in the delta or records in the proposal,
  under "Related requirements", a one-line reason to leave it.
- At the confirmation pause the user sees those related requirements next to
  the new ones, so a contradiction is caught before design rather than in
  review.

## Context

**Observed:**
- `src/specworks/skills/specworks-specify/SKILL.md` step 2: "Inspect the
  code, tests and docs the change touches (read-only), and the living specs
  of related capabilities" with `specworks spec show <ref>` and
  `specworks spec list`; nothing asks for requirements about the same
  command or key, nor a decision per requirement.
- `specworks spec` has `show` and `list` only (`src/specworks/cli/specs.py`);
  there is no search across living requirements.
- The proposal template (`src/specworks/templates/proposal.md`) and its
  instruction (`src/specworks/schema.yaml`) have Why, What Changes,
  Capabilities, Impact, Out of Scope.
- Living docs: `src/specworks/specs/docs` (specs), `src/specworks/cli/docs`
  (cli), `src/specworks/workflow/docs` (workflow).

**Assumed:**
- A literal, case-insensitive search on the change's own terms finds the
  requirements that matter; the agent and the user judge each match.

## Constraints

- [hard] Read-only; paths relative to the workspace root.
- [hard] Errors are values (`{"error": ...}`, exit 1 under `--json`); no
  match is an empty result, not an error.
- [hard] Files read with `encoding="utf-8"`.
- [soft] Output in the style of `spec list`.

## Options

### Option A: `spec find` plus skill text and a proposal section

`specworks spec find <term>... [--json]` lists every living requirement of
the workspace (every module) whose title, text or scenarios contain a term
(literal, case-insensitive, any term): capability ref, ID, title, and the
first matching line with its number. Specify runs it with the change's
terms and decides per match; the proposal gets a "Related requirements"
section; step 5's table shows them.

- **Pros:** deterministic, cheap search; judgement stays with agent and user.
- **Cons:** the agent picks the terms.
- **Effort:** S-M
- **Touches:** specs, cli, workflow, skills
- **Outcomes:** meets all three.

### Option B: skill text only

Specify reads every living spec and searches it itself.

- **Pros:** no code.
- **Cons:** many tokens on a large project; depends on the agent reading all.
- **Effort:** S
- **Touches:** skills
- **Outcomes:** all three, less reliably.

### Option C: a `specworks check` warning

Warn when a backticked term of the delta appears in a living requirement the
delta does not modify.

- **Pros:** automatic.
- **Cons:** noisy on common terms (`--json`, `--change`); no reason recorded.
- **Effort:** M
- **Touches:** specs
- **Outcomes:** the first and third automatically; not the second.

## Recommendation

Option A, agreed with the user. Out of scope: searching active changes'
deltas, fuzzy or regex matching, and a `check` warning (a later change if A
is not enough).

## Open Questions

- None blocking the proposal.

## Candidate Capabilities

- `specs`: modified - finding living requirements by term.
- `cli`: modified - the `spec find` command.
- `workflow`: modified - the proposal's "Related requirements" section
  (template and instruction).
