# Review: project-docs

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **code-gap** AC-PROJ-029.3: a capability on path `.` does not load: validate_relative refuses `.` for a capability path (src/specworks/core/config.py:325, src/specworks/core/validators.py:20), so `context` fails with "capability 'core' path must be a relative folder inside the project, got '.'"; REQ-PROJ-029 says it SHALL load and share the module's docs folder (test tests/test_modules.py:519 fails)
  - **Proposal**: back to code: accept `.` as a capability path when the config is loaded (e.g. an allow_dot flag on validate_relative used only at config.py:325); module paths, docs_dir, tests_dir and a capability's tests keep refusing `.`; `capability add --path .` stays as it is (a candidate for a later change)
  - **Decision**: back to code: accept '.' as a capability path when the config is loaded only; module paths, docs_dir, tests_dir and a capability's tests keep refusing it; capability add --path . stays as it is
- [ ] R2 **test-gap** The existing test test_no_skill_mentions_architecture_md (tests/test_skills.py:661-664) asserts no skill mentions architecture.md ('architecture.md was never written'); this change makes close, adopt, start and the five reading skills mention `<docsPath>/architecture.md` by design (pinned wording, REQ-PROJ-029), so it fails for 8 skills
  - **Proposal**: back to test: remove test_no_skill_mentions_architecture_md, whose premise this change reverses; the new wording tests (tests/test_skills.py:1205-1222) cover what the skills say about the architecture, and test_close_keeps_one_block_diagram_of_the_capability_in_the_living_design still keeps a capability's diagram in its design.md
  - **Decision**: back to test: remove test_no_skill_mentions_architecture_md from tests/test_skills.py; its premise is reversed by this change and the new wording tests pin what the skills say
  - done in test: removed test_no_skill_mentions_architecture_md from tests/test_skills.py; its premise is reversed by this change and the new wording tests pin what the skills say
- [ ] R3 **code-gap** The start skill's guardrail was reworded to "`module add`, `capability add --create`, `config set` and `diagrams --dir`" (src/specworks/skills/specworks-start/SKILL.md:188), breaking the pinned wording START_CREATE_WORDING checked verbatim by test_the_start_skill_creates_the_code_folders_with_capability_add_create (tests/test_skills.py:1033)
  - **Proposal**: back to code: keep the pinned phrase verbatim and add the new command after it, e.g. "`skills --tools`, `module add`, `capability add --create` and `config set`, plus `diagrams --dir` for the architecture's diagram; `init` is the user's", then refresh the installed copies with `uv run specworks skills`
  - **Decision**: back to code: keep the pinned START_CREATE_WORDING phrase in specworks-start exactly and add diagrams --dir after it, then refresh the installed copies with uv run specworks skills
- [ ] R4 **quality** architecture_diagrams_current names the fix as `specworks diagrams --dir docs` (src/specworks/workflow/validate.py:45, REQ-FLOW-013), which is the wrong folder for a module (`services/billing/docs`) or a project whose docs_dir is not `docs`
  - **Proposal**: back to code: build the command from the module's docs folder, `specworks diagrams --dir <ws.rel(ctx.module.docs_path)>`
  - **Decision**: back to code: build the --dir of validate's architecture warning from the module's docs folder instead of the hard-coded docs

## Changed files without tags

- `tests/helpers.py`: test helper: `make_repo` writes the sample `docs/architecture.md`, so the existing close tests keep passing with REQ-CLI-007's refusal (task 2.1)
- `tests/samples.py`: test data: the sample `ARCHITECTURE` text used by `tests/helpers.py` (task 2.1)
- `tests/test_walkthrough.py`: the end-to-end walkthrough writes the module's architecture before `close`, as the close skill does (plumbing for REQ-CLI-007, no criterion of its own)

## Summary

The suite had 10 failures when the halves met: a capability on `.` still refused at load (R1), an older skill test that this change's pinned wording contradicts (R2), and a pinned phrase of the start skill broken by a rewording (R3); reading the diff added the hard-coded `--dir docs` in validate's new warning (R4). Nothing fixed in review (inside /specworks-build): R1, R3 and R4 go back to code, R2 back to test; no spec or design change proposed. Candidate for a later change: `capability add --path .`.
