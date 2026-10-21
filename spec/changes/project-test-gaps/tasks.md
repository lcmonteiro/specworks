# Tasks: project-test-gaps

## 1. Archive order

- [ ] 1.1 Write a test in `tests/test_archive.py` for AC-PROJ-012.2 (two changes archived on different days, listed oldest first) tagged `@ac`; it passes against the current code, so verify it fails when the listing order is reversed by hand, then restore it
- [ ] 1.2 Confirm `list_archived` keeps its `@req REQ-PROJ-012` tag (REQ-PROJ-012); verify `specworks trace` lists its code

## 2. `dark_theme: none`

- [ ] 2.1 Write a test for AC-PROJ-003.5's `dark_theme: none` part (the config loads, the dark theme reads as none, and the render options carry no `--dark-theme`) tagged `@ac`; verify it passes, and fails if `none` is rejected
