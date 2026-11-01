# Tasks: specify-related-requirements

## 1. Finding requirements

- [x] 1.1 Add the stubs in design.md's Interfaces: `RequirementMatch` and `find_requirements` (returning `[]`) in `src/specworks/specs/capabilities.py` (REQ-SPECS-016); verify `specworks run lint` passes
- [ ] 1.2 [test] Tests for AC-SPECS-016.1 to AC-SPECS-016.6 on sample projects (a term in a requirement's text in another case, a term only in a scenario, two terms in two requirements listed once each, a module's capability as `billing:<name>`, no match empty, an empty term refused with the pinned message), asserting path, line and text, tagged `@ac`; verify they fail on the stub
- [x] 1.3 [code] Implement `find_requirements` as design.md decides (casefold substrings, the block from header to end, first matching line, workspace order, skip a missing living spec), tagged `@req REQ-SPECS-016`; verify `specworks run lint` passes and, in this repository, `uv run python -c` calling it for `config set` lists REQ-CLI-013

## 2. The command

- [x] 2.1 Add the stub `spec_find` in `src/specworks/cli/specs.py` as `spec find` (REQ-CLI-016); verify `specworks spec find --help` shows the terms argument
- [ ] 2.2 [test] Tests for AC-CLI-016.1 to AC-CLI-016.4 (text lines with `path:line`, JSON fields with relative paths, the no-match line and empty `matches`, no term refused with `{"error": ...}` and exit 1), tagged `@ac`; verify they fail on the stub
- [x] 2.3 [code] Implement `spec find` as design.md decides (text, JSON, no match, no term), tagged `@req REQ-CLI-016`; verify `specworks run lint` passes and `uv run specworks spec find "config set"` prints REQ-CLI-013's line

## 3. The proposal and the specify skill

- [ ] 3.1 [test] Wording tests in `tests/test_skills.py` (or the template tests) for the phrases pinned in design.md: the specify skill, `templates/proposal.md` and the proposal instruction in `schema.yaml` (REQ-SPECS-016); verify they fail on the current text
- [x] 3.2 [code] Add the `## Related requirements` section to `src/specworks/templates/proposal.md` and the bullet to the proposal instruction in `src/specworks/schema.yaml`, and rewrite specify's steps 2 and 5 with the pinned wording, then refresh the installed copies with `uv run specworks skills` (REQ-SPECS-016); verify `uv run specworks instructions proposal --change specify-related-requirements --json` shows the bullet and the section
