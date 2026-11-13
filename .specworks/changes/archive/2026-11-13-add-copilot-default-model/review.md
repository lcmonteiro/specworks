# Review: add-copilot-default-model

Base: `<!-- base branch -->`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **spec-gap** REQ-HARNESS-013 needs a model marked is_chat_default, but bmw.ghe.com marks none (checked live with a stored login), so login then harness still fails there, missing the refinement's first outcome
  - **Proposal**: back to specify: when no model is marked as the default chat model, use the first model of the list that the model picker shows, whose policy is enabled and that is not a preview, in the versatile category, else the first such model of any category; fail only when there is none
  - **Decision**: back to specify: when no model is marked as the default chat model, use the first model the picker shows (model_picker_enabled), whose policy is enabled and that is not a preview, in the versatile category, else the first such model of any category; fail naming both settings only when there is none (agreed with the user)
  - done in specify: REQ-HARNESS-013 falls back to the first usable picker model (policy enabled, not a preview), versatile first; AC-HARNESS-013.3 reworded, AC-HARNESS-013.4 and AC-HARNESS-013.5 added; tasks 5.1 and 5.2
  - done in design: no API change: default_model() keeps its signature; its Decision in design.md describes the picker fallback
  - done in test: AC-HARNESS-013.4 and AC-HARNESS-013.5 tested; AC-HARNESS-013.3 cases now lists with no usable picker model
  - done in code: default_model() falls back to the first usable picker model, versatile first; live bmw.ghe.com check gives claude-sonnet-5.5
  - confirmed in review: done: REQ-HARNESS-013 falls back to the first usable picker model; AC-HARNESS-013.4/.5 tested; live bmw.ghe.com gives claude-sonnet-5.5

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

- `tests/support/copilot.py`: test helper of REQ-HARNESS-013 (the fake GitHub answers `/models`)

## Summary

Cycle 1 found one spec gap (R1): bmw.ghe.com marks no default chat model, so REQ-HARNESS-013 was sent back to specify and now falls
back to the first usable picker model, versatile first. Cycle 2 carried it through design (no API change), test and code; the full suite
passes, and a live bmw.ghe.com login with no model named gets `claude-sonnet-5.5`. Both halves were written by the coordinator after the
phase subagents stalled, so tests and code are not independent readings of the spec. No other drift found.
