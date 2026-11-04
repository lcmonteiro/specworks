# Review: tighten-telemetry-tests

Base: `c9f6407`

## Findings

None.

## Changed files without tags

- `tests/test_skills.py`: not part of this change. It comes from `start-without-capabilities` (commits ff5437e, f326074), merged into `main` after this change started, so it shows in the diff against base `c9f6407`; this change touches only `tests/cli/test_telemetry.py` and `tests/integrations/test_langfuse.py` (both tagged `@ac`). The same goes for the other files of that change in the base diff (skills, README, docs, schema, templates).

## Summary

The change only adds checks. `tests/integrations/test_langfuse.py:128` now asserts `elapsed < 7` (AC-INTEG-009.3) against the 5 s `TIMEOUT` in `src/specworks/tools/langfuse.py:26`, and `tests/cli/test_telemetry.py:285` covers AC-CLI-019.2 with equal creation times, so a `traceId` difference can only come from the module label. Both tests assert their THEN through the public interface and would fail if the behaviour broke. No drift between code, specs and design (no interfaces); the full suite passes (998).
