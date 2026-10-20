# Refinement: module-interface-paths

## Problem

The design gate checks that every file named under Interfaces in design.md
exists, but for a change in a module it also accepts a file found at the
workspace root. Reproduced: a `billing` change (module at `services/billing`)
naming `src/invoices.py` passes "every file named under Interfaces exists"
although billing has no `src/`. The top level's `src/invoices.py` satisfies it,
so a missing stub goes unnoticed. This was found as suspected bug 6 of
`baseline-workflow`.

## Context

**Observed:**
- `workflow/gate.py`, `interface_files_exist`: a named path counts if
  `(ctx.module.root / path)` or `(ctx.ws.root / path)` exists.
- Accepting both presumably lets a module's design name files module-relative
  (`src/invoices.py`) or workspace-relative (`services/billing/src/invoices.py`,
  the form every CLI path is printed in).
- A change belongs to one module. Work across modules lives at the top level, or
  in the lowest module that contains every part, so a module's interfaces lie
  inside its folder.
- Living spec of `workflow`: REQ-FLOW-006 (Gate design). AC-FLOW-006.2 says the
  named files must exist, relative to nothing in particular. Its tests
  (`tests/test_design_phase.py`) use a top-level project only.

**Assumed:**
- Existing designs name files in one of the two forms, inside their module.

## Constraints

- [hard] A module's change passes the check only when the files exist inside
  that module.
- [hard] Both ways of writing a path keep working, and top-level changes behave
  as today.
- [soft] The rule is stated in REQ-FLOW-006.

## Options

### Option A: Keep both roots, document it

- **Pros:** No code change.
- **Cons:** The false pass stays.
- **Effort:** S
- **Touches:** `workflow`

### Option B: Module-relative paths only

- **Pros:** Simple and strict.
- **Cons:** **BREAKING** for designs that name files workspace-relative.
- **Effort:** S
- **Touches:** `workflow`

### Option C: Both forms, but the file must be inside the module

A path counts if, read module-relative or workspace-relative, it names an
existing file inside the change's module folder.

- **Pros:** Removes the false pass, and keeps both forms and top-level changes
  working.
- **Cons:** Slightly more logic, plus one rule to state in the spec.
- **Effort:** S
- **Touches:** `workflow`

## Recommendation

**Option C**, chosen with the user. It removes exactly the false pass and
breaks no design that is correct today.

## Open Questions

None.

## Candidate Capabilities

- `workflow`: REQ-FLOW-006 MODIFIED, with a new criterion: in a module's change,
  a named file must exist inside the module, written either way.
