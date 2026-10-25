# Review: refactor-check-delta

Base: `origin/main`

## Findings

None.

Checked: `Issue.level` is `Literal["error", "warning"]` and `Issue.error` / `Issue.warning` match design.md `## Interfaces`; no `Issue("error"/"warning", ...)` call is left in `src` or `tests`; the `err` / `warn` closures are gone. The split of `_check_delta` keeps the original order of checks (format, registration, per requirement: header, living / conflicts, MODIFIED, REMOVED, body), the same messages and the same skips (`continue` on a missing ID and after REMOVED). `tests/` is unedited and the suite passes (546 tests); lint and mypy are clean; `check.py` coverage is 99%.

## Changed files without tags

None: every changed source file carries `@req` tags (`src/specworks/specs/check.py`).

## Summary

No drift between code, design and the (skipped) specs: a pure refactor with the same issues, messages and order. Nothing sent back to an earlier phase.
