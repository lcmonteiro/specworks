# Review: dedupe-copilot-skills

Base: `origin/main`

## Findings

- [x] R1 **test-gap** AC-PROJ-022.2: the test's GIVEN does not hold. The `workspace` fixture runs `init`, which now saves `tools: [claude, copilot]`; the test then appends a second `tools:` entry, so the config has two `tools:` keys, `save_tools` replaces the first, the reload still reads the second, and `save_tools` (rightly) restores the file and raises. Both cases (`flow`, `block`) fail. The code does what REQ-PROJ-022 says (`tests/test_modules.py:85-94`)
  - **Proposal**: back to test: set the GIVEN with `set_saved_tools(workspace, saved_value)` (one `tools:` entry, `[claude]` as a flow list and as a block list) instead of appending to the config; the assertions stay as they are
  - **Decision**: back to test: set the GIVEN with `set_saved_tools` (one `tools:` entry, flow and block forms); assertions unchanged (agreed with the user)
  - done in test: the GIVEN is set with `set_saved_tools(workspace, saved)` (`[claude]` flow, `\n  - claude` block), one `tools:` entry; assertions unchanged (`tests/test_modules.py:84-93`). Confirmed in review cycle 2: both cases pass
- [x] R2 **test-gap** AC-INTEG-005.6: the setup writes `.github/prompts/<name>.prompt.md` without creating `.github/prompts/`, which `init --tools all` no longer creates (no prompt files since REQ-INTEG-005), so the test fails with `FileNotFoundError` before the command runs. The code removes those files as the criterion says (`tests/test_skills.py:565-582`, line 573)
  - **Proposal**: back to test: create `.github/prompts/` (`mkdir(parents=True, exist_ok=True)`) before writing the old prompt files; the assertions stay as they are
  - **Decision**: back to test: create `.github/prompts/` before writing the old prompt files; assertions unchanged (agreed with the user)
  - done in test: the test creates `.github/prompts/` (`mkdir(parents=True, exist_ok=True)`) before writing the old prompt files; assertions unchanged (`tests/test_skills.py:573`). Confirmed in review cycle 2: it passes
- [x] R3 **spec-gap** REQ-PROJ-022 says "when the edit would not give the expected config, it SHALL leave the file unchanged and say to set `tools` by hand", but no criterion covers it, so no test does: once R1 is fixed the restore path of `save_tools` runs in no test (`src/specworks/core/config_file.py:193-199`). The other config edits have one (AC-PROJ-008.4). It is reachable only with a hand-edited config (e.g. two `tools:` keys); overall branch coverage stays at 98%
  - **Proposal**: back to specify: add AC-PROJ-022.3 "A list the text edit cannot replace" (GIVEN a config with two `tools:` entries, WHEN the tool `copilot` is saved, THEN the config is unchanged and the error says to set `tools` by hand), then its test in the test half; no code change. Alternative: accepted, as a safety net for hand-broken configs
  - **Decision**: back to specify: add AC-PROJ-022.3 "A list the text edit cannot replace" (GIVEN a config with two `tools:` entries, WHEN the tool `copilot` is saved, THEN the config is unchanged and the error says to set `tools` by hand), then its test; no code change (agreed with the user)
  - done in specify: added AC-PROJ-022.3 "A list the text edit cannot replace" to REQ-PROJ-022 and test task 1.4; no other spec change
  - done in design: no new API; AC-PROJ-022.3 is reached through `save_tools`, which raises `ConfigError` (set `tools` by hand) and restores the file, as the Decision "Saving edits the config as text" says; design.md `## Interfaces` now names that error on the `save_tools` entry; no stub changes
  - done in test: `test_saving_the_tools_leaves_a_config_it_cannot_edit_unchanged` (`@ac AC-PROJ-022.3`, `tests/test_modules.py:98-107`) writes a second `tools:` entry, checks that `save_tools` raises `ConfigError` saying to set `tools` by hand and that the file is byte-for-byte unchanged; it would fail if the restore were dropped. Confirmed in review cycle 2: it passes, and the restore path of `save_tools` now runs in a test

## Changed files without tags

- `tests/helpers.py`: test helper (`set_saved_tools`) used by the tests of AC-PROJ-003.6, AC-PROJ-003.7, AC-INTEG-004.5-7, AC-INTEG-006.6, AC-CLI-003.12 and AC-CLI-009.3/5; no behaviour of its own

## Summary

Cycle 1 found three findings: two tests not updated for this change's own
behaviour (R1, R2, back to test) and a missing criterion for the restore path
of `save_tools` (R3, AC-PROJ-022.3 added in specify, its test in the test
half). Cycle 2 carried all three out with test changes only; the review
confirmed each, the suite passes (660 tests) with lint and typecheck, and no
new finding came up. No code, design or API change in cycle 2.
