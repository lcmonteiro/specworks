# Tasks: add-capability-create

## 1. capability add --create

- [x] 1.1 Add the `--create` option to `capability_add` in `src/specworks/cli/project.py` as a stub that accepts the flag and creates nothing yet, and the `created` JSON field as `null` (REQ-CLI-014); verify `specworks capability add --help` shows `--create`
- [x] 1.2 [test] Tests for AC-CLI-014.1 to AC-CLI-014.6 (a missing folder created with an empty `.gitkeep` and `created` naming it; an existing folder unchanged and `created` null; `--module billing`; a refused prefix creating nothing; a path that is a file refused with the pinned fragment, file and config unchanged; no folder without `--create`), tagged `@ac`; verify they fail on the stub
- [ ] 1.3 [code] Implement `--create` as design.md decides (the file check before registering, creation after, the `created` field and text line), tagged `@req REQ-CLI-014`; verify `specworks run lint` passes and, in a scratch project, `specworks capability add auth --path src/auth --create --json` creates `src/auth/.gitkeep` and prints `"created": "src/auth/.gitkeep"`

## 2. The start skill

- [x] 2.1 [test] Wording tests in `tests/test_skills.py` for the phrases pinned in design.md and that `specworks-start/SKILL.md` no longer contains ``write an empty `.gitkeep` `` (REQ-CLI-014); verify they fail on the current skill
- [ ] 2.2 [code] Rewrite step 5, the Boundary and the Guardrails of `src/specworks/skills/specworks-start/SKILL.md` with the pinned wording, then refresh the installed copies with `uv run specworks skills` (REQ-CLI-014); verify `grep -n 'create' .claude/skills/specworks-start/SKILL.md` shows each phrase
