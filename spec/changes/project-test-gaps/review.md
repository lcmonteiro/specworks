# Review: project-test-gaps

Base: `origin/main`

## Findings

None.

## Changed files without tags

None: both changed test files carry the new tags.

## Summary

Tests only, no code change. AC-PROJ-012.2 gets a new test with changes
archived on two days, whose names sort the other way, so only the date order
can pass it; reversing the listing by hand made it fail. AC-PROJ-003.5's
`dark_theme: none` part was already exercised by `test_theme_by_name_or_number`
(no `--dark-theme` in the render) and `test_list_themes_shows_the_one_in_use`
(reads back as `none`); both now carry the tag, and both failed when `none` was
rejected by hand. No findings.
