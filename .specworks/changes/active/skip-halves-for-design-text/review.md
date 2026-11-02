# Review: skip-halves-for-design-text

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **design-gap** design.md Interfaces says 'No new command, option or function', but review.py adds two public module functions, route() and next_step() (REQ-FLOW-010, src/specworks/workflow/review.py:235 and :246); they are used only inside review.py, whose other internal helpers are private (_find, _insert, _tick, _write)
  - **Proposal**: back to code: rename them _route and _next_step, so the agreed API (Finding.design_only and its designOnly key, nothing else) holds; no test imports them
  - **Decision**: back to code: rename route() and next_step() in src/specworks/workflow/review.py to _route and _next_step, as design.md adds no new function
  - done in code: renamed route() and next_step() in src/specworks/workflow/review.py to _route and _next_step; no other module uses them
- [ ] R2 **quality** three places that list the Decision forms still omit 'back to design only:' (REQ-FLOW-016): the help of 'finding decide' (src/specworks/cli/workflow.py:180), the Decision comment in the review template (src/specworks/templates/review.md:12) and the review instruction (src/specworks/schema.yaml:266)
  - **Proposal**: back to code: name 'back to design only: ...' (design, then review) next to 'back to <step>: ...' in all three
  - **Decision**: back to code: name 'back to design only:' among the Decision forms in the finding decide help (src/specworks/cli/workflow.py), the review template comment (src/specworks/templates/review.md) and the review instruction (src/specworks/schema.yaml)
  - done in code: named 'back to design only:' (design, then review) among the Decision forms in the finding decide help (src/specworks/cli/workflow.py), the review template comment (src/specworks/templates/review.md), the review instruction (src/specworks/schema.yaml) and the decide_finding docstring
- [ ] R3 **spec-gap** AC-FLOW-016.5's WHEN still says a decision is refused when it is 'neither back to <step>: nor accepted:', which literally covers 'back to design only:' and so contradicts AC-FLOW-016.7 and the REQ-FLOW-016 text (specs/workflow/spec.md, AC-FLOW-016.5); the code and its test follow 016.7
  - **Proposal**: back to specify: reword AC-FLOW-016.5's WHEN to 'a decision is not back to <step>:, back to design only: or accepted:' (MODIFIED REQ-FLOW-016, same IDs); no code or test change
  - **Decision**: back to specify: reword the WHEN of AC-FLOW-016.5 to name all three Decision forms (back to <step>:, back to design only:, accepted:) in the MODIFIED REQ-FLOW-016, same IDs; no code or test change
  - done in specify: AC-FLOW-016.5's WHEN now names all three Decision forms (back to <step>:, back to design only:, accepted:) in the MODIFIED REQ-FLOW-016, same IDs; no code or test change
  - done in design: nothing to change in design.md: Interfaces and Decisions > The Decision form already name the three forms and the refusal before any write; no API change

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

None: `specworks review` lists no untraced source or test file. The four
skill files (`src/specworks/skills/specworks-{review,build}/SKILL.md` and
their installed copies under `.claude/skills/`) are Markdown, never scanned
for tags; `tests/test_skills.py` checks their pinned wording.

## Summary

<!-- Two or three lines: what was found, what changed in code, specs and design, and anything sent back to an earlier phase. -->

The suite passes (884 tests) and every requirement and criterion is tagged.
Three open findings, nothing fixed here: R1 (two helpers left public against
"no new function") and R2 (help, template and instruction miss the new form)
go back to code; R3 (AC-FLOW-016.5 contradicts AC-FLOW-016.7) goes back to specify.
