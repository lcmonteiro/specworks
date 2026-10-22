# Proposal: refactor-check-delta

## Why

`_check_delta` in `src/specworks/specs/check.py` is about 115 lines mixing five concerns, and `Issue("error"/"warning", ...)` is repeated about 30 times with an untyped `level`. Each new rule makes it longer and harder to review.

## What Changes

- `Issue.level` is typed `Literal["error", "warning"]`, and `Issue.error(file, line, message)` and `Issue.warning(...)` constructors replace the repeated `Issue("error", ...)` calls in `check.py`.
- `_check_delta` is split into one function per concern: delta format, living-spec and capability registration, conflicts with other active changes, per-requirement ADDED / MODIFIED / REMOVED rules, and requirement body. The inner `err` and `warn` closures go away.
- No behaviour change: the same issues, messages and order.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Behaviour is unchanged, so the change is marked `specworks skip-specs`.

## Impact

- `src/specworks/specs/check.py`, and `src/specworks/specs/trace.py` only if it builds an `Issue` directly (it does not today).
- The existing `@req REQ-SPECS-005`, `REQ-SPECS-006` and `REQ-SPECS-007` tags move with the code they describe.
- The public names `Issue`, `check_change`, `collect`, `other_deltas` and `ChangeSpecs` are unchanged.

## Out of Scope

- Changing any check, message or severity.
- Splitting `_check_tasks`, `check_change` or other functions.
- Moving code to other modules.
