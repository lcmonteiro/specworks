# Refinement: refactor-check-delta

## Problem

`_check_delta` in `src/specworks/specs/check.py` is about 115 lines of nested branches that mix five concerns, and its inner `err` and `warn` closures are redefined on every call. `Issue("error", ...)` and `Issue("warning", ...)` are repeated about 30 times across the module, and `level` is a bare `str`, so a typo passes mypy. Each new rule makes the function longer. From the review: "Split `_check_delta` into the five concerns above, and share the `Issue` helpers."

## Context

**Observed:**
- Capability `specs` (`src/specworks/specs`, prefix `SPECS`, has a living spec). `_check_delta` carries `@req REQ-SPECS-005, REQ-SPECS-006, REQ-SPECS-007`.
- Public surface of `check.py`: `Issue`, `check_change`, `collect`, `other_deltas`, `ChangeSpecs`. `trace.py` imports `ChangeSpecs`, `Issue`, `check_change` and `other_deltas`; `tests/test_close_phase.py` imports `collect`.
- `_check_delta` is private; tests reach it only through `check_change` and the CLI. Only `tests/test_propose.py:563` reads an issue by position, from a filtered `warnings` list.
- Consumers read `Issue.level` as `"error"` or `"warning"` (`cli/specs.py`, `trace.py`).
- The five concerns in `_check_delta`:
  1. delta format (problems, no requirements, wrong section)
  2. living-spec state and capability registration (living-spec problems, new capability, prefix clash)
  3. conflicts with other active changes (ADDED claimed, MODIFIED/REMOVED claimed, closed since)
  4. per-requirement ADDED / MODIFIED / REMOVED rules
  5. requirement body (SHALL or MUST, length, scenarios, WHEN/THEN)
- Baseline: 546 tests pass, ruff and mypy clean, 98% branch coverage.

**Assumed:**
- Issue order within a delta is not relied on by tests beyond what is observed above, but it is user-visible output, so it is kept identical anyway.

## Constraints

- [hard] No behaviour change: same issues, same messages, same order.
- [hard] Branch coverage stays at 95% or above; ruff and mypy stay clean.
- [hard] Existing `@req` tags stay on the code that implements them.
- [soft] Change only `check.py`, plus `trace.py` if the `Issue` helpers touch it.
- [soft] Keep the public names above unchanged.

## Options

### Option A: Small helpers and a split

Add `Issue.error(file, line, message)` and `Issue.warning(...)` constructors and type `level` as `Literal["error", "warning"]`. Split `_check_delta` into one function per concern, sharing a small context object (`file`, `issues`, `seen`, living IDs).

- **Pros:** output identical; removes the string literals and the per-call closures; low risk.
- **Cons:** a context object adds a small type; the order of the calls must be kept to preserve issue order.
- **Effort:** S
- **Touches:** `specs`

### Option B: A `DeltaChecker` class

A class holding `ws`, `change`, `delta`, `seen`, `issues`, `living_ids` and `others` as state, with one method per concern.

- **Pros:** no parameter passing.
- **Cons:** a bigger rewrite for one function; hidden shared state.
- **Effort:** M
- **Touches:** `specs`

### Option C: Do nothing

- **Pros:** the function works and is fully covered.
- **Cons:** every new rule makes it longer.
- **Effort:** S
- **Touches:** none

## Recommendation

Option A, agreed with the user. It fixes both problems with the least risk and keeps the output identical.

## Open Questions

- Should the change be marked `specworks skip-specs` (no behaviour change)? Proposed yes. (who can answer: the user)

## Candidate Capabilities

- `specs`: modified (internal refactor only; no requirement changes, hence `skip-specs`)
