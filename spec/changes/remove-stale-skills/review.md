# Review: remove-stale-skills

Base: `origin/main`

## Findings

- [x] R1 **quality** a stale `specworks-*` skill folder that is a symlink makes `shutil.rmtree` raise `OSError` ("Cannot call rmtree on a symbolic link"), so `specworks skills` crashes instead of removing the link (REQ-INTEG-005; `src/specworks/tools/skills.py`, `remove_stale_skills`)
  - **Decision**: back to code: unlink a symlinked stale skill (its target is untouched), and add a test with a symlinked stale skill (agreed with the user)
  - done in code: `remove_stale_skills` unlinks a symlinked stale skill instead of `rmtree`; `test_a_stale_skill_that_is_a_symlink_is_unlinked_not_followed` checks the link is removed and its target kept (it fails without the fix)
  - **Resolved** in cycle 2: code fixed and confirmed in review.

## Changed files without tags

The base `origin/main` also lacks the closed changes on this branch
(ignore-sample-tags and the baselines):

- `tests/helpers.py`: only `specworks: ignore-tags` markers from
  ignore-sample-tags.
- `tests/test_walkthrough.py`: only the ignore block from ignore-sample-tags.

Checked against REQ-INTEG-005 (MODIFIED) and design.md:
- AC-INTEG-005.6: `remove_stale_skills` deletes, in each chosen tool's skills
  folder, the folders named `specworks-*` or in `RETIRED_NAMES` (`sw-refine`)
  that aren't shipped, and the matching Copilot prompt files. It returns them,
  and `write_skills` prints `removed <path>` before installing. The test plants
  `specworks-propose`, `sw-refine` and a user's `my-skill` in all three places:
  the first two are removed and printed, `my-skill` and every shipped skill
  stay. Since R1, a symlinked stale skill is unlinked and its target kept.
- The interfaces match design.md (`remove_stale_skills`, `RETIRED_NAMES`,
  `install_skills` unchanged). Only the chosen tools' folders are scanned.
- All 50 tests in `tests/test_skills.py` pass (AC-INTEG-005.1 to .5 included),
  and so do the full suite and lint.

## Summary

Stale specworks skills are now removed on install or refresh, and reported. R1
(a symlinked stale skill crashed the removal) was fixed in cycle 2.
