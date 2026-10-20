# Review: remove-stale-skills

Base: `origin/main`

## Findings

- [ ] R1 **quality** a stale `specworks-*` skill folder that is a symlink makes `shutil.rmtree` raise `OSError` ("Cannot call rmtree on a symbolic link"), so `specworks skills` crashes instead of removing the link (REQ-INTEG-005; `src/specworks/tools/skills.py`, `remove_stale_skills`)
  - **Decision**: back to code: unlink a symlinked stale skill (its target is untouched), and add a test with a symlinked stale skill (agreed with the user)
  - done in code: `remove_stale_skills` unlinks a symlinked stale skill instead of `rmtree`; `test_a_stale_skill_that_is_a_symlink_is_unlinked_not_followed` checks the link is removed and its target kept (it fails without the fix)

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

## Summary

`remove_stale_skills` and the `removed` lines implement AC-INTEG-005.6. R1 goes
back to code for symlinked skill folders.
