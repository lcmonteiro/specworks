# Review: add-expected-outcomes

Base: `origin/main`

## Findings

- [ ] R1 **quality** `specworks-refine` agrees the outcomes in step 3 but two other places of the same skill still leave them out: the "No premature solution" principle says "the problem and constraints come before the options" (no outcomes), and step 5's summary lists the problem, the options, the recommendation and the open questions, so the user never sees the agreed outcomes when the refinement is recorded (`src/specworks/skills/specworks-refine/SKILL.md:28`, `:121`; no requirement: `skip-specs`)
  - **Proposal**: back to code: the principle says "the problem, its outcomes and the constraints come before the options"; step 5 summarizes "the problem in one line, the outcomes, the options, ..."; refresh the installed copies with `uv run specworks skills`; no test change needed (alternative: accept as it is, step 3 already says outcomes come before the options)

## Changed files without tags

None: `specworks review` lists no file under untracedSource or untracedTests. The change is `skip-specs`; its changed files are the refinement template, `schema.yaml`, three skills and their installed copies (text, never scanned for tags), and `tests/test_skills.py`, whose new wording checks need no `@ac` (no requirement).

## Summary

The template, the refinement and proposal instructions and the refine, specify and baseline skills say what the proposal lists, and the new wording checks in `tests/test_skills.py` assert each of those points; the suite (626 tests) and lint pass. One quality finding (R1): two places in the refine skill do not mention the outcomes yet, proposed back to code.
