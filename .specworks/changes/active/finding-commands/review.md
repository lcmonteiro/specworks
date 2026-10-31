# Review: finding-commands

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **quality** _locate crashes with StopIteration (a traceback, not a FindingError or {"error": ...}) when an ID is repeated and the repeated block has a Decision line: next(...) over review.blocks finds no entry for the second block (src/specworks/workflow/review.py:405); decide, done and close all call _locate (REQ-FLOW-016, REQ-CLI-011)
  - **Proposal**: code: track the current block's ID in _locate and record Decision lines only for the block kept in review.blocks (the first one), so a repeated ID reads like parse_review and any refusal is a FindingError
  - **Decision**: back to code: _locate tracks which finding the current block belongs to and records Decision lines only for the first block with that ID, so a repeated ID is a FindingError, not a traceback (agreed with the user)
  - done in code: _locate tracks the ID of the block it reads and records Decision lines only for the first block with that ID, so decide, done and close on a repeated ID no longer crash
  - confirmed in review: _locate records Decision lines only for the first block with an ID (review.py:399-407); on a sample review.md with R1 repeated and a Decision under the second block, finding decide, done and close each exit 0 on the first R1 with no traceback
- [x] R2 **quality** decide_finding replaces only the first line of an existing Decision (src/specworks/workflow/review.py:512): a hand-wrapped Decision keeps its continuation lines under the new one, and when such a line holds another 'back to <step>:' the read-back refuses, so the finding cannot be decided again without a hand edit (REQ-FLOW-016)
  - **Proposal**: accept: wrapped hand-written Decisions are rare, the read-back refuses safely and leaves review.md unchanged; or replace the Decision item with its more-indented continuation lines
  - **Decision**: accepted: a hand-wrapped Decision is rare, the commands write one-line Decisions, and the read-back check refuses an edit that would misroute it, leaving review.md unchanged (agreed with the user)
- [x] R3 **code-gap** add_finding refuses a finding whose Proposal (or text) names another step in the 'back to <step>:' form, e.g. a code-gap proposing to go back to implement (with the colon): it fails with 'its phase reads implement, not code', because parse_review routes on that form anywhere in the block while add_finding expects TYPE_PHASE[kind] (src/specworks/workflow/review.py:493); the review and build skills tell review to record its proposals in that very form, and this review's own first finding was refused that way (REQ-FLOW-016, AC-FLOW-016.1)
  - **Proposal**: code: in add_finding expect the phase parse_review gives the new lines (the step named by the form in the proposal or text, else TYPE_PHASE[kind]) instead of refusing; test: a test under AC-FLOW-016.1 adding a code-gap whose proposal routes it to implement, expecting R3 open and routed to implement
  - **Decision**: back to implement: add_finding expects the step the reader gives (a 'back to <step>:' in its proposal or text routes it), with a test under AC-FLOW-016.1 (agreed with the user)
  - done in implement: code: add_finding expects the step the reader gives, the last 'back to <step>:' in its text or proposal, else the type's step
  - confirmed in review: add_finding expects the step parse_review gives, the last 'back to <step>:' in its text or proposal, else the type's step (review.py:495-497); test_ac_flow_016_1_a_proposal_naming_another_step_routes_the_new_finding adds a code-gap proposing back to implement and reads R3 open, routed to implement

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

None: `specworks review` lists no untracedSource or untracedTests. The skill
texts (`src/specworks/skills/`, `.claude/skills/`) are Markdown, never scanned
for tags; tests/test_skills.py checks their wording (task 3.1).

## Summary

<!-- Two or three lines: what was found, what changed in code, specs and design, and anything sent back to an earlier phase. -->

Cycle 1 found three findings: R1 (a crash on a repeated ID) and R3
(add_finding refused a proposal in the `back to <step>:` form) went back to
code and implement; R2 (a wrapped Decision not fully replaced) was accepted.
Cycle 2 confirmed R1 and R3 fixed and closed them; there are no new findings.
The suite passes (727), lint and typecheck pass, branch coverage is 97%,
every requirement and criterion is tagged, and the interfaces match
design.md. No spec or design change. Notes for a later change: no test
covers the repeated-ID path R1 fixed; under `--json` the `finding` commands'
`path` (review.md, as design.md specifies) replaces the change's own `path`;
`None.` under Findings is kept when a finding is added; and a new review.md's
`Base:` line is left as the template's placeholder.
