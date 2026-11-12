# Review: add-copilot-default-model

Base: `<!-- base branch -->`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **spec-gap** REQ-HARNESS-013 needs a model marked is_chat_default, but bmw.ghe.com marks none (checked live with a stored login), so login then harness still fails there, missing the refinement's first outcome
  - **Proposal**: back to specify: when no model is marked as the default chat model, use the first model of the list that the model picker shows, whose policy is enabled and that is not a preview, in the versatile category, else the first such model of any category; fail only when there is none
  - **Decision**: back to specify: when no model is marked as the default chat model, use the first model the picker shows (model_picker_enabled), whose policy is enabled and that is not a preview, in the versatile category, else the first such model of any category; fail naming both settings only when there is none (agreed with the user)

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

- `tests/support/copilot.py`: test helper of REQ-HARNESS-013 (the fake GitHub answers `/models`)

## Summary

<!-- Two or three lines: what was found, what changed in code, specs and design, and anything sent back to an earlier phase. -->
