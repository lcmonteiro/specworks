# Tasks: narrow-spec-find

## 1. Searching without the markup

- [ ] 1.1 Add `search_requirements`, `RequirementSearch` and `BroadTerm` to `src/specworks/specs/capabilities.py` as stubs, `find_requirements` unchanged (REQ-SPECS-016); verify `specworks run lint` and the existing tests pass
- [ ] 1.2 [test] Write failing tests for AC-SPECS-016.7 in `tests/test_find_requirements.py`, tagged `@ac AC-SPECS-016.7`: `requirement` and `scenario` find nothing, `when` finds only the requirement whose text says it, at that line; an ID and a scenario title still find theirs; verify they fail for the right reason
- [ ] 1.3 [test] Write failing tests for AC-SPECS-016.8 in `tests/test_find_requirements.py`, tagged `@ac AC-SPECS-016.8`: with three requirements, `token` (2 of 3) is broad with its counts and `expired` (1 of 3) is not, and all three are listed; verify they fail for the right reason
- [ ] 1.4 [code] Implement `search_requirements`: remove the markup at the start of each line before comparing, count each term's requirements in the same scan, report broad terms, and make `find_requirements` return its matches (REQ-SPECS-016), tagged `@req REQ-SPECS-016`; verify with lint and `specworks spec find requirement when` on this repo

## 2. The warning in `spec find`

- [ ] 2.1 [test] Write failing tests for AC-CLI-016.5 in `tests/test_find_requirements.py`, tagged `@ac AC-CLI-016.5`: the text output lists the matches and the warning naming the broad term with its count, exit 0; `--json` has `broad` with `term`, `matches` and `of`, empty for a narrow term; verify they fail for the right reason
- [ ] 2.2 [code] Print the broad-term warning and add `broad` to `--json` in `spec find` (REQ-CLI-016), tagged `@req REQ-CLI-016`; verify with lint and `specworks spec find shall` and `specworks spec find --json "spec find"` on this repo
