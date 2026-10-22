# Design: refactor-check-delta

## Context

`_check_delta` in `src/specworks/specs/check.py` mixes five concerns and builds issues through two inner closures; `Issue("error"/"warning", ...)` is repeated about 30 times with an untyped `level`. See proposal.md for the motivation. Constraint: no behaviour change (same issues, messages and order), 95% branch coverage, existing `@req` tags stay on the code they describe.

## Goals / Non-Goals

**Goals:**
- Type `Issue.level` and give `Issue` two constructors so call sites stop repeating the level string.
- One private function per concern of `_check_delta`.

**Non-Goals:**
- Changing any check, message or severity.
- Splitting `_check_tasks` or `check_change`, or moving code to other modules.

## Decisions

- **Option A** (refinement.md, agreed with the user): constructors on `Issue` and a split of `_check_delta`, not a `DeltaChecker` class.
- **Constructors as classmethods** (`Issue.error`, `Issue.warning`) taking `(file, line, message)`: the order of the dataclass fields without `level`, so every call site is the old call minus its first argument.
- **Split functions are private** and are not part of the interface: they share the delta, a small context (`file`, `issues`, `seen`, living IDs) and are called in the current order so issue order is preserved. The code half decides their exact names and parameters.

## Interfaces

- `src/specworks/specs/check.py`: `Issue.level: Literal["error", "warning"]` (was `str`); `Issue(level, file, line, message)` is otherwise unchanged
- `src/specworks/specs/check.py`: `Issue.error(file: str, line: int, message: str) -> Issue` (classmethod), same as `Issue("error", file, line, message)`
- `src/specworks/specs/check.py`: `Issue.warning(file: str, line: int, message: str) -> Issue` (classmethod), same as `Issue("warning", file, line, message)`

Unchanged public names: `Issue`, `check_change`, `collect`, `other_deltas`, `ChangeSpecs`. Not breaking: existing `Issue("error", ...)` callers still work. Agreed with the user (the constructors are named in the proposal and refinement).

## Risks / Trade-offs

- [issue order changes when the concerns are split] -> call the extracted functions in the original order; the existing tests and CLI output stay unedited.
- [`Literal` rejects a non-literal `level` in mypy] -> no caller passes a variable (checked in `src/` and `tests/`).
