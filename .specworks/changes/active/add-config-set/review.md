# Review: add-config-set

Base: `origin/main`

## Findings

- [ ] R1 **spec-gap** REQ-PROJ-025 says a command with no line yet goes under the existing `commands:` block, but no criterion covers it and no test runs it (`src/specworks/core/config_file.py:276`): it is the path `config set commands.typecheck`/`commands.build` takes on the default config from init, which is what adopt does
  - **Proposal**: back to specify: add AC-PROJ-025.10 A command added to the commands block (GIVEN the default config written by init, WHEN commands.typecheck is set to `uv run mypy`, THEN the config loads with that typecheck command, test and lint unchanged, one `typecheck:` line, its comments kept), then its test
  - **Decision**: back to specify: add AC-PROJ-025.10 (a command added to an existing commands: block) and its test
- [ ] R2 **spec-gap** REQ-PROJ-025 says an edit that would not load leaves the file unchanged with an error saying to set the key by hand; a context over MAX_CONTEXT_BYTES is refused before writing with `'context' is larger than 51200 bytes` instead (`src/specworks/core/config_file.py:221`), as design.md decides, and no criterion or test covers it
  - **Proposal**: back to specify: add to REQ-PROJ-025 that a context over the config's size limit is refused before writing, naming the limit, with a criterion AC-PROJ-025.11 (file unchanged), then its test
  - **Decision**: back to specify: add the context size limit (refused before writing) to REQ-PROJ-025 with AC-PROJ-025.11 and its test
- [ ] R3 **test-gap** No test runs three error paths of REQ-PROJ-025/REQ-CLI-013: the restore when the edited file fails to load (`src/specworks/core/config_file.py:240`, e.g. a 4-space `commands:` block, which gets a 2-space line), a context added to a config with no `context:` (`config_file.py:291`), and an unreadable `--file` (`src/specworks/cli/project.py:357`, `cannot read <file>`, config unchanged)
  - **Proposal**: back to test: add these three tests in tests/test_config_set.py, asserting the config file is unchanged on each error; tag the restore test AC-PROJ-025.9 (an entry the text edit cannot change) and the context-added test AC-PROJ-025.6
  - **Decision**: back to test: add tests for the restore after a load failure, a context added to a config with no context: line, and an unreadable --file
- [x] R4 **code-gap** REQ-PROJ-025 says the user's comments are kept, but a comment at the end of the line that is replaced is dropped: ` test: # fill in` becomes ` test: pytest`, `context: | # note` becomes `context: |` (`src/specworks/core/config_file.py:274`, `:289`)
  - **Proposal**: accepted: the comment is about the value being replaced, and telling a comment from a `#` in an unquoted command needs a YAML parse of the line; init writes no such comments
  - **Decision**: accepted: a trailing comment on the replaced line is about the old value, and init writes none
- [ ] R5 **design-gap** design.md (The check after writing) says the expected context is `None` when the text is empty; the code expects `""` (`src/specworks/core/config_file.py:220`), which is what `context: |` alone loads as, so the code is right and the Decision is wrong
  - **Proposal**: back to design: in The check after writing, say the expected context is an empty string when the text is empty (`context: |` alone loads as ""); no code change
  - **Decision**: back to design: fix the Decision 'The check after writing' to say an empty context is expected as an empty string, as the code does

## Changed files without tags

None: `specworks review` lists no untraced source or test file. The skill
files (`src/specworks/skills/**`, `.claude/skills/**`) are Markdown, which is
never scanned for tags; their wording is checked by `tests/test_skills.py`.

## Summary

The suite passes (783 tests) and every requirement and criterion is tagged;
the code matches the Interfaces in design.md. Five findings, all open with a
proposal for the user: two spec-gaps (adding a command to an existing
`commands:` block, and the context size limit, have no criterion: back to
specify), one test-gap (three untested error paths: back to test), one
code-gap proposed as accepted (an inline comment on the replaced line is
dropped) and one design-gap (the empty-context expectation in a Decision:
back to design). Nothing was changed in code, specs or design here.
Out of scope, for a later change: matching the indent of an existing
`commands:` block (a 4-space block is refused today and restored).
