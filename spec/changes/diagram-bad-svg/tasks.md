# Tasks: diagram-bad-svg

## 1. SVGs that can't be stamped

- [ ] 1.1 Write a failing test in `tests/test_diagrams.py` for AC-INTEG-003.4 (a fake d2 that writes an unclosed `<?xml`, non-UTF-8 output, or no file, next to a good diagram; no file expects d2's own message) tagged `@ac`; verify it fails with the crash
- [ ] 1.2 Read and stamp the SVG inside `render`'s error handling, turning an unreadable file and an unclosed declaration into a `DiagramError` (REQ-INTEG-003) tagged `@req REQ-INTEG-003`; verify the 1.1 test and the existing AC-INTEG-003.x tests pass
