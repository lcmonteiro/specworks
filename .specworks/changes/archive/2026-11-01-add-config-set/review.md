# Review: add-config-set

Base: `origin/main`

## Findings

- [x] R1 **spec-gap** REQ-PROJ-025 says a command with no line yet goes under the existing `commands:` block, but no criterion covers it and no test runs it (`src/specworks/core/config_file.py:276`): it is the path `config set commands.typecheck`/`commands.build` takes on the default config from init, which is what adopt does
  - **Proposal**: back to specify: add AC-PROJ-025.10 A command added to the commands block (GIVEN the default config written by init, WHEN commands.typecheck is set to `uv run mypy`, THEN the config loads with that typecheck command, test and lint unchanged, one `typecheck:` line, its comments kept), then its test
  - **Decision**: back to specify: add AC-PROJ-025.10 (a command added to an existing commands: block) and its test
  - done in specify: added AC-PROJ-025.10 (a command added to the commands block) and task 4.1 for its test
  - done in design: no API change: the Decision 'Writing a command' already puts a new key after the commands block's last indented line, the path AC-PROJ-025.10 covers
  - done in implement: no code change: set_config_value already adds a command after the commands block's last indented line; checked on a scratch init config (commands.typecheck added as one line, the rest unchanged)
  - confirmed in review: AC-PROJ-025.10 added to REQ-PROJ-025; tests/test_config_set.py test_ac_proj_025_10_* add commands.typecheck to the default init config and to a filled commands block (one typecheck: line, one commands: line, test and lint unchanged, comments kept); they pass
- [x] R2 **spec-gap** REQ-PROJ-025 says an edit that would not load leaves the file unchanged with an error saying to set the key by hand; a context over MAX_CONTEXT_BYTES is refused before writing with `'context' is larger than 51200 bytes` instead (`src/specworks/core/config_file.py:221`), as design.md decides, and no criterion or test covers it
  - **Proposal**: back to specify: add to REQ-PROJ-025 that a context over the config's size limit is refused before writing, naming the limit, with a criterion AC-PROJ-025.11 (file unchanged), then its test
  - **Decision**: back to specify: add the context size limit (refused before writing) to REQ-PROJ-025 with AC-PROJ-025.11 and its test
  - done in specify: REQ-PROJ-025 now refuses a context over the size limit before writing, naming it; added AC-PROJ-025.11 and task 4.1 for its test
  - done in design: no API change: the Decision 'The keys' already refuses a context over MAX_CONTEXT_BYTES before writing, with load_config's message naming the limit (AC-PROJ-025.11)
  - done in implement: no code change: set_config_value already refuses a context over MAX_CONTEXT_BYTES before writing, naming the limit; checked on a scratch config (refused, file unchanged)
  - confirmed in review: REQ-PROJ-025 now refuses a context over the size limit before writing, naming it (AC-PROJ-025.11); test_ac_proj_025_11_a_context_over_the_size_limit_is_refused asserts the limit in the error and the file unchanged; it passes
- [x] R3 **test-gap** No test runs three error paths of REQ-PROJ-025/REQ-CLI-013: the restore when the edited file fails to load (`src/specworks/core/config_file.py:240`, e.g. a 4-space `commands:` block, which gets a 2-space line), a context added to a config with no `context:` (`config_file.py:291`), and an unreadable `--file` (`src/specworks/cli/project.py:357`, `cannot read <file>`, config unchanged)
  - **Proposal**: back to test: add these three tests in tests/test_config_set.py, asserting the config file is unchanged on each error; tag the restore test AC-PROJ-025.9 (an entry the text edit cannot change) and the context-added test AC-PROJ-025.6
  - **Decision**: back to test: add tests for the restore after a load failure, a context added to a config with no context: line, and an unreadable --file
  - done in test: added tests for the restore after a load failure (4-space commands: block, AC-PROJ-025.9), a context added to a config with no context: line (AC-PROJ-025.6) and an unreadable --file (AC-CLI-013.2), each asserting the config file unchanged on error
  - confirmed in review: tests added and passing: the restore after a load failure on a 4-space commands: block (AC-PROJ-025.9), a context added to a config with no context: line (AC-PROJ-025.6), an unreadable --file refused with cannot read and the config unchanged (AC-CLI-013.2)
- [x] R4 **code-gap** REQ-PROJ-025 says the user's comments are kept, but a comment at the end of the line that is replaced is dropped: ` test: # fill in` becomes ` test: pytest`, `context: | # note` becomes `context: |` (`src/specworks/core/config_file.py:274`, `:289`)
  - **Proposal**: accepted: the comment is about the value being replaced, and telling a comment from a `#` in an unquoted command needs a YAML parse of the line; init writes no such comments
  - **Decision**: accepted: a trailing comment on the replaced line is about the old value, and init writes none
- [x] R5 **design-gap** design.md (The check after writing) says the expected context is `None` when the text is empty; the code expects `""` (`src/specworks/core/config_file.py:220`), which is what `context: |` alone loads as, so the code is right and the Decision is wrong
  - **Proposal**: back to design: in The check after writing, say the expected context is an empty string when the text is empty (`context: |` alone loads as ""); no code change
  - **Decision**: back to design: fix the Decision 'The check after writing' to say an empty context is expected as an empty string, as the code does
  - done in design: fixed the Decision 'The check after writing': an empty context is expected as an empty string, as the code does; no API or code change
  - done in implement: no code change: the code already expects an empty string for an empty context, as the fixed Decision says
  - confirmed in review: design.md 'The check after writing' now says an empty context is expected as an empty string, matching config_file.py:220; no code change needed

## Changed files without tags

None: `specworks review` lists no untraced source or test file. The skill
files (`src/specworks/skills/**`, `.claude/skills/**`) are Markdown, which is
never scanned for tags; their wording is checked by `tests/test_skills.py`.

## Summary

Cycle 1 found five: two spec-gaps (adding a command to an existing
`commands:` block, and the context size limit, had no criterion: back to
specify), one test-gap (three untested error paths: back to test), one
code-gap accepted (an inline comment on the replaced line is dropped: it is
about the old value, and init writes none) and one design-gap (the
empty-context expectation in a Decision: back to design).

Cycle 2 confirmed each one carried out and closed them: REQ-PROJ-025 gained
AC-PROJ-025.10 and AC-PROJ-025.11 with passing tests, the three error paths
have tests asserting the config unchanged, and design.md's Decision matches
the code. No new drift: the code is unchanged since cycle 1, every
requirement has code and every criterion a test, and the suite passes (789
tests). Nothing was changed here beyond review.md.
Out of scope, for a later change: matching the indent of an existing
`commands:` block (a 4-space block is refused today and restored).
