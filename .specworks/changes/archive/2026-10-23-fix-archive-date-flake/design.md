# Design: fix-archive-date-flake

## Context

See [proposal.md](proposal.md). Only a test module changes.

## Goals / Non-Goals

**Goals:**
- The archive tests give the same result at any time of day.

**Non-Goals:**
- Changing how the archive code reads the date.

## Decisions

### Patch `date` in `specworks.specs.merge` instead of freezing time

The archive folder name comes from `date.today()` in `merge.py`; a `date`
subclass with a fixed `today()` pins it without a new dependency. Alternative:
a time-freezing library: one more dev dependency for one module.

## Interfaces

None: no function, command or data shape is added or changed.

## Risks / Trade-offs

- [The fixture patches a module-level name] -> if `merge.py` stops importing
  `date` by name, the fixture fails loudly (`monkeypatch.setattr` raises on a
  missing attribute).

## Open Questions

- None.
