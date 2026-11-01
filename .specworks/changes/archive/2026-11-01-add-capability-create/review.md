# Review: add-capability-create

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **quality** With --create, a --path whose parent exists as a file (a file `src`, `--path src/auth`) passes the file check, the config is written, then mkdir raises an uncaught NotADirectoryError: a traceback with exit 1 and no {"error": ...} under --json, and the capability stays registered; REQ-CLI-014 says a path that exists as a file is refused before the config is written and a refused add creates nothing (`src/specworks/cli/project.py:337`)
  - **Proposal**: back to implement: code: before add_capability_entry, with --create, refuse when the code folder or any of its parents below the module root exists and is not a folder, with the existing ConfigError '<that path> exists and is not a folder; give <name> another --path' (path relative to the workspace root); test: a test under AC-CLI-014.5 with a file `src` and `--path src/auth --create --json` asserting {"error": ...} naming src, exit 1, the file and the config unchanged
  - **Decision**: back to implement: before registering, refuse when the code folder or any parent below the module root exists and is not a folder (ConfigError naming it), plus a test under AC-CLI-014.5 with a file src and --path src/auth
  - done in implement: code: capability_add refuses with --create when the code folder or any parent below the module root exists and is not a folder (ConfigError naming it, e.g. 'src exists and is not a folder; give auth another --path'), before the config is written
  - confirmed in review: confirmed in cycle 2: capability_add refuses with --create when the code folder or any parent below the module root exists and is not a folder, before add_capability_entry (src/specworks/cli/project.py:337-339); test_ac_cli_014_5_a_parent_of_the_path_that_is_a_file_is_refused (tests/test_capability_add.py) asserts the error naming src, exit 1, the file, the config and the registry unchanged; suite passes (802 tests)

## Changed files without tags

None: `specworks review` lists no untracedSource or untracedTests. The skill
files (`src/specworks/skills/specworks-start/SKILL.md` and its installed copy
`.claude/skills/specworks-start/SKILL.md`) are Markdown, never scanned for
tags; their pinned wording is checked by the tests in `tests/test_skills.py`.

## Summary

Cycle 1: the suite passed (801 tests) and every requirement and criterion
was tagged; `capability_add` matches design.md's interface and Decisions,
and the start skill carries the pinned wording, with its installed copy
refreshed. One quality finding (R1, a parent of `--path` that is a file
crashed after the config was written) went back to implement.

Cycle 2: implement carried out R1 (the parent check before the config is
written, and a second AC-CLI-014.5 test with a file `src`); R1 is closed.
The suite passes (802 tests), `specworks review` lists no drift candidates,
and reading the cycle's diff found no new finding. No spec, design or code
change was made in review; nothing was accepted.
