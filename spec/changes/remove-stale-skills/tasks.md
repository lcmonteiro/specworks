# Tasks: remove-stale-skills

## 1. Stale skills

- [x] 1.1 Add `remove_stale_skills` and `RETIRED_NAMES` as stubs (REQ-INTEG-005); verify the existing tests still pass
- [ ] 1.2 Write a failing test in `tests/test_skills.py` for AC-INTEG-005.6 (stale `specworks-propose` and `sw-refine` skill folders and prompt files plus a user's `my-skill`, then `specworks skills --tools all`) tagged `@ac`; verify it fails because nothing is removed
- [ ] 1.3 Implement `remove_stale_skills` and print `removed <path>` from `write_skills` (REQ-INTEG-005) tagged `@req REQ-INTEG-005`; verify the 1.2 test and the existing AC-INTEG-005.x tests pass
