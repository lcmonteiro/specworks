# Review: dedupe-copilot-skills

Base: `origin/main`

## Findings

- [ ] R1 **test-gap** AC-PROJ-022.2: the test's GIVEN does not hold. The `workspace` fixture runs `init`, which now saves `tools: [claude, copilot]`; the test then appends a second `tools:` entry, so the config has two `tools:` keys, `save_tools` replaces the first, the reload still reads the second, and `save_tools` (rightly) restores the file and raises. Both cases (`flow`, `block`) fail. The code does what REQ-PROJ-022 says (`tests/test_modules.py:85-94`)
  - **Proposal**: back to test: set the GIVEN with `set_saved_tools(workspace, saved_value)` (one `tools:` entry, `[claude]` as a flow list and as a block list) instead of appending to the config; the assertions stay as they are
  - **Decision**: back to test: set the GIVEN with `set_saved_tools` (one `tools:` entry, flow and block forms); assertions unchanged (agreed with the user)
- [ ] R2 **test-gap** AC-INTEG-005.6: the setup writes `.github/prompts/<name>.prompt.md` without creating `.github/prompts/`, which `init --tools all` no longer creates (no prompt files since REQ-INTEG-005), so the test fails with `FileNotFoundError` before the command runs. The code removes those files as the criterion says (`tests/test_skills.py:565-582`, line 573)
  - **Proposal**: back to test: create `.github/prompts/` (`mkdir(parents=True, exist_ok=True)`) before writing the old prompt files; the assertions stay as they are
  - **Decision**: back to test: create `.github/prompts/` before writing the old prompt files; assertions unchanged (agreed with the user)
- [ ] R3 **spec-gap** REQ-PROJ-022 says "when the edit would not give the expected config, it SHALL leave the file unchanged and say to set `tools` by hand", but no criterion covers it, so no test does: once R1 is fixed the restore path of `save_tools` runs in no test (`src/specworks/core/config_file.py:193-199`). The other config edits have one (AC-PROJ-008.4). It is reachable only with a hand-edited config (e.g. two `tools:` keys); overall branch coverage stays at 98%
  - **Proposal**: back to specify: add AC-PROJ-022.3 "A list the text edit cannot replace" (GIVEN a config with two `tools:` entries, WHEN the tool `copilot` is saved, THEN the config is unchanged and the error says to set `tools` by hand), then its test in the test half; no code change. Alternative: accepted, as a safety net for hand-broken configs

## Changed files without tags

- `tests/helpers.py`: test helper (`set_saved_tools`) used by the tests of AC-PROJ-003.6, AC-PROJ-003.7, AC-INTEG-004.5-7, AC-INTEG-006.6, AC-CLI-003.12 and AC-CLI-009.3/5; no behaviour of its own

## Summary

The code matches the delta specs and design.md (interfaces, decisions, the
question at init, the saved choice, one folder for both tools); lint and
typecheck pass. The suite has 3 failures, all in tests not updated for
behaviour this change introduced (R1, R2): both go back to the test half. R3
proposes a criterion (and test) for the restore path of `save_tools`, which
REQ-PROJ-022 states but no scenario covers.
