# Refinement: finding-commands

## Problem

The agents write every line of a change's `review.md` by hand: new findings
with their Proposal (review), Decision lines (the build coordinator, or
review on its own), `done in <step>:` lines (specify, design, test, code) and
the tick with what review confirmed. Reading those lines is deterministic
(`parse_review`, `gate review`, `specworks cycle`), writing them is not: in
the last builds about 15 lines were written with ad-hoc scripts, and a
malformed line only shows up when the gate runs. It is slow and fragile, and
the user wants the process as safe, deterministic and fast as possible.
(Source: user request in session, paraphrased; item 3 of the sequence in
`deterministic-steps`.)

## Outcomes

- `specworks finding add --change <ref> <type> "<text>" --proposal
  "<proposal>"` adds `- [ ] R<next> **<type>** <text>` and its
  `**Proposal**:` line under `## Findings`, with the next free ID; it refuses
  an unknown type, and creates `review.md` with its headings when it does not
  exist yet.
- `specworks finding decide R<n> --change <ref> "<decision>"` writes, or
  replaces, the finding's `**Decision**:` line; it accepts only `back to
  <step>: …` or `accepted: …`, and `accepted` ticks the box; it refuses an
  unknown finding or step.
- `specworks finding done R<n> --in <step> --change <ref> "<what>"` adds
  `done in <step>: <what>` under the finding.
- `specworks finding close R<n> --change <ref> "<what was confirmed>"` ticks
  the finding and records what review confirmed.
- Every other line of `review.md` is left as it was, and `gate review` and
  `specworks cycle` read the result as they read hand-written lines today.
- The review, build, specify, design, test and code skills use these
  commands instead of editing those lines.
- `--json` returns the finding as `specworks cycle` sees it; errors are
  values (`{"error": …}`, exit 1), as in every command.

## Context

**Observed:**
- `src/specworks/workflow/review.py`: `parse_review` / `read_review`
  (REQ-FLOW-010) read findings (`FINDING_RE`), types (`TYPE_PHASE`: spec-gap,
  design-gap, test-gap, code-gap, tag, quality), `back to <step>:`
  (`BACK_RE`) and `done in <step>:` (`DONE_RE`); `gate review` checks them
  (REQ-FLOW-011); `specworks cycle` routes them (REQ-FLOW-012).
- `specworks review` is already the drift command (REQ-FLOW-009), so the new
  commands need their own group: `finding`.
- The skills that write review.md lines: `specworks-review`,
  `specworks-build` step 3 and `_shared/phase-subagents.md` (Decision),
  `specworks-specify` step 2 and the build's "done in" rule.
- The config edits (`save_tools`, REQ-PROJ-022) already edit a file as text,
  reload it and restore it when the result is not what was expected.

**Assumed:**
- A finding's block is its checkbox line plus the indented lines under it,
  as the parser reads it today.

## Constraints

- [hard] Existing review.md files (hand-written and archived) stay readable;
  the parser does not change what it accepts.
- [hard] Every other line of the file, including the user's edits and a
  finding's free text, is left exactly as it was.
- [hard] Files are read and written with `encoding="utf-8"`.
- [soft] The commands follow the CLI's conventions: `--change`, `--json`,
  errors as values, paths relative to the workspace root.

## Options

### Option A: Edit the text in place and check the result

Each command finds the finding's block with the parser, inserts or replaces
one line, parses the result again and writes it only when it reads back as
expected; otherwise it refuses and leaves the file as it was.

- **Pros:** keeps the format and every existing review.md; safe through the
  read-back check; same approach as the config edits.
- **Cons:** text editing has edge cases (bullets, bold IDs) to test.
- **Effort:** M
- **Touches:** `workflow`, `cli`
- **Outcomes:** meets all seven.

### Option B: A data file, with review.md generated

Findings live in `review.yaml`; `review.md` is written from it.

- **Pros:** fully structured.
- **Cons:** changes every change's format; archived files and hand edits no
  longer match the data.
- **Effort:** L
- **Touches:** `workflow`, `cli`, `specs`
- **Outcomes:** meets 1-4 and 6-7; fails the first constraint.

### Option C: One command with flags

`specworks finding set R1 --decision … | --done-in … | --close …`.

- **Pros:** one command.
- **Cons:** the same work as A in a form harder to discover and to name in
  the skills.
- **Effort:** M
- **Touches:** `workflow`, `cli`
- **Outcomes:** meets all seven.

## Recommendation

Option A, agreed with the user: it keeps the current format and every
existing review.md, and the read-back check makes each write safe.

## Open Questions

- The rest of the sequence from `deterministic-steps` (`specworks commit`,
  `config set`, `capability add --create`, an option for `new` not to switch
  branch, shared rule text) stays for later changes. Not blocking. (who can
  answer: maintainer)

## Candidate Capabilities

- `workflow`: modified - writing findings, decisions and their follow-ups to
  review.md
- `cli`: modified - the `finding` command group
