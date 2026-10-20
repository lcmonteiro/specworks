# Refinement: diagram-bad-svg

## Problem

When d2 succeeds but writes an SVG specworks can't stamp, `specworks diagrams`
crashes with a raw traceback. Reproduced: a d2 that writes
`<?xml version="1.0"<svg/>` (the declaration never closed) gives
`ValueError: substring not found`, and the other diagrams of the run are never
rendered. This was found as suspected bug 8 of `baseline-integrations`.

## Context

**Observed:**
- `tools/diagrams.py`, `render`: calls pyd2 inside a `try` that turns
  `pyd2.D2Error` and `OSError` into a `DiagramError`, then reads the SVG and
  stamps it **outside** that `try`.
- `stamp`: for an SVG starting with `<?xml`, it finds the end of the
  declaration with `svg_text.index("?>")`, which raises `ValueError` when the
  declaration is not closed.
- The same unprotected read crashes when d2 writes no file (`FileNotFoundError`)
  or a file that isn't UTF-8 (`UnicodeDecodeError`).
- `cli/specs.py`, `diagrams`: catches `DiagramError` per diagram, marks it
  `error` with the message, goes on with the next one, and exits 1.
- Living spec of `integrations`: REQ-INTEG-003 reports a missing d2, a d2 that
  doesn't run, and a d2 compile error as errors naming the diagram, but not a
  bad output.

**Assumed:**
- pyd2's own d2 always writes a well-formed SVG. This needs a broken or custom
  d2 (`SPECWORKS_D2`) or a pyd2 bug, so it is rare.

## Constraints

- [hard] No traceback: every render failure is a `DiagramError` naming the
  diagram, and the other diagrams still render.
- [hard] A well-formed SVG is stamped exactly as today.

## Options

### Option A: An unreadable or unstampable SVG is a render error

Reading and stamping the SVG join the render's error handling. An unclosed
declaration, a missing output file or non-UTF-8 output each give
`cannot render <name>.d2: …`.

- **Pros:** One rule closes all three crashes, the same way d2's other failures
  are reported.
- **Cons:** None. The broken file stays on disk, as after a compile error.
- **Effort:** S
- **Touches:** `integrations`

### Option B: Only fix the unclosed declaration

Put the stamp at the start of the file when the declaration has no end.

- **Pros:** Smallest change.
- **Cons:** The stamp before a declaration makes invalid XML, and the other two
  crashes stay.
- **Effort:** S
- **Touches:** `integrations`

### Option C: Leave it

- **Pros:** No change.
- **Cons:** A traceback, and the rest of the run skipped.
- **Effort:** S
- **Touches:** none

## Recommendation

**Option A**, chosen with the user. One small fix covers the three crashes and
matches how REQ-INTEG-003 already treats d2's failures.

## Open Questions

None.

## Candidate Capabilities

- `integrations`: REQ-INTEG-003 MODIFIED, with a new criterion: d2 succeeds but
  its SVG can't be read or stamped.
