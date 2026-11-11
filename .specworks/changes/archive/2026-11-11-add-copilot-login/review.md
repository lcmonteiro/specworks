# Review: add-copilot-login

Base: `origin/main`

## Findings

- [x] R1 **design-gap** The missing-key error reads `SPECWORKS_MODEL_API_KEY is not set (or run `specworks login copilot`)`, while design.md ## Interfaces for model.py says `... is not set (run specworks login copilot)`; REQ-HARNESS-010 / AC-HARNESS-010.2 and AC-CLI-022.2 are met by both (src/specworks/harness/model.py:26)
  - **Proposal**: back to design only: reword the Interfaces line to the message the code gives (`is not set (or run `specworks login copilot`)`), which reads better and keeps the spec's two facts
  - **Decision**: back to design only: reword the Interfaces line of design.md to the code's message, 'SPECWORKS_MODEL_API_KEY is not set (or run `specworks login copilot`)'
  - done in design: design.md Interfaces line now reads the code's message
  - confirmed in review: design.md Interfaces line reads the code's message ('... is not set (or run `specworks login copilot`)', model.py:26); confirmed
- [x] R2 **quality** `specworks login` without the harness extra fails with the harness command's text, `specworks harness needs the harness extra: install specworks[harness]`, naming the wrong command (REQ-CLI-023, AC-CLI-023.10; src/specworks/cli/login.py:39, src/specworks/cli/harness.py:10)
  - **Proposal**: back to code: give login its own message, `specworks login needs the harness extra: install specworks[harness]`, keeping `specworks[harness]` and no Python version; `harness` keeps its text
  - **Decision**: back to code: give login its own missing-extra message, 'specworks login needs the harness extra: install specworks[harness]'
  - done in code: login has its own EXTRA_MISSING message
  - confirmed in review: login has its own EXTRA_MISSING ('specworks login needs the harness extra: install specworks[harness]', login.py:16); harness keeps its text; confirmed, suite passes

## Changed files without tags

- `tests/support/copilot.py`: helper of the tests for REQ-HARNESS-011, REQ-HARNESS-012 and REQ-CLI-023 (a fake GitHub on a fake transport and a fake clock); it holds no test of its own.

## Summary

The suite passes (1170 tests) and every requirement has code and every criterion a test. Two small findings from the first review, both carried out in cycle 2 and confirmed here: R1 (design-gap, design.md's key-error wording, fixed in design) and R2 (quality, `login` named `harness` when the extra is missing, fixed in code). No spec change.
Candidate for a future change, not a finding: `specworks login copilot --ghe-host <host>` reuses a working login stored for another host (REQ-HARNESS-011 reuses any login that still gives a token), so a different host needs `--force`.
