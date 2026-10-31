# Review: finding-commands

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **quality** _locate crashes with StopIteration (a traceback, not a FindingError or {"error": ...}) when an ID is repeated and the repeated block has a Decision line: next(...) over review.blocks finds no entry for the second block (src/specworks/workflow/review.py:405); decide, done and close all call _locate (REQ-FLOW-016, REQ-CLI-011)
  - **Proposal**: code: track the current block's ID in _locate and record Decision lines only for the block kept in review.blocks (the first one), so a repeated ID reads like parse_review and any refusal is a FindingError
- [ ] R2 **quality** decide_finding replaces only the first line of an existing Decision (src/specworks/workflow/review.py:512): a hand-wrapped Decision keeps its continuation lines under the new one, and when such a line holds another 'back to <step>:' the read-back refuses, so the finding cannot be decided again without a hand edit (REQ-FLOW-016)
  - **Proposal**: accept: wrapped hand-written Decisions are rare, the read-back refuses safely and leaves review.md unchanged; or replace the Decision item with its more-indented continuation lines
- [ ] R3 **code-gap** add_finding refuses a finding whose Proposal (or text) names another step in the 'back to <step>:' form, e.g. a code-gap proposing to go back to implement (with the colon): it fails with 'its phase reads implement, not code', because parse_review routes on that form anywhere in the block while add_finding expects TYPE_PHASE[kind] (src/specworks/workflow/review.py:493); the review and build skills tell review to record its proposals in that very form, and this review's own first finding was refused that way (REQ-FLOW-016, AC-FLOW-016.1)
  - **Proposal**: code: in add_finding expect the phase parse_review gives the new lines (the step named by the form in the proposal or text, else TYPE_PHASE[kind]) instead of refusing; test: a test under AC-FLOW-016.1 adding a code-gap whose proposal routes it to implement, expecting R3 open and routed to implement
  - **Decision**: back to implement: add_finding expects the step the reader gives (a 'back to <step>:' in its proposal or text routes it), with a test under AC-FLOW-016.1 (agreed with the user)

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

None: `specworks review` lists no untracedSource or untracedTests. The skill
texts (`src/specworks/skills/`, `.claude/skills/`) are Markdown, never scanned
for tags; tests/test_skills.py checks their wording (task 3.1).

## Summary

<!-- Two or three lines: what was found, what changed in code, specs and design, and anything sent back to an earlier phase. -->

The suite passes (726), every requirement and criterion is tagged, and the
interfaces match design.md. Three findings, all open for the next cycle: R3
(add_finding refuses a proposal in the `back to <step>:` form the skills ask
for) needs code and a test; R1 (a crash on a repeated ID) needs code; R2 (a
wrapped Decision is not fully replaced) is proposed as accepted. No spec or
design change. Out of scope, for a later change: `None.` under Findings is
kept when a finding is added, and a new review.md's `Base:` line is left as
the template's placeholder.
