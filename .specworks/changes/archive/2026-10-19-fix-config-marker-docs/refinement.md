# Refinement: fix-config-marker-docs

## Problem

The module docstring of `src/specworks/core/config.py` says "the first line
`specworks: 1` marks the file as a specworks config". The code accepts the
marker on any line, and the living spec says the same. Anyone reading the
docstring gets the rule wrong. This was found as suspected bug 2 of
`baseline-project`.

## Context

**Observed:**
- `core/config.py:25`: `MARKER_RE = ^specworks:[ \t]*\d+[ \t]*(#.*)?$` with
  `re.MULTILINE`. An unindented `specworks: <n>` line (an optional trailing
  comment allowed) counts anywhere in the file. An indented, nested key never
  counts.
- `core/docs/spec.md`, REQ-PROJ-001: a config is a `<dir>.yml` "holding a
  `specworks: <n>` line", without saying which line. Its tests
  (AC-PROJ-001.1, AC-PROJ-001.2) agree.
- The README and the packaged skills don't describe the marker's position.
  `init` writes it as the first line (`core/config_file.py`), which a reader may
  have taken for a rule.

**Assumed:**
- Some configs may carry a comment or a `# yaml-language-server` line above
  the marker, which the current behaviour supports.

## Constraints

- [hard] No behaviour change: configs found today stay found.
- [soft] The docstring states the rule exactly as the code applies it.

## Options

### Option A: Fix the docstring

Reword it as "a `specworks: <n>` line (not indented) marks the file", with no
code or spec change. The change is marked skip-specs.

- **Pros:** Code, spec and docs agree, and nothing breaks.
- **Cons:** None.
- **Effort:** S
- **Touches:** `project` (docs only)

### Option B: Require the marker on the first line

Change REQ-PROJ-001 (MODIFIED) and `is_config_file` so only the first line
counts.

- **Pros:** Stricter, and matches the old wording.
- **Cons:** **BREAKING**: a config with anything above the marker would
  silently stop being found (`"root": null`). It protects against little: an
  unindented `specworks:` key in an unrelated YAML file is already unlikely.
- **Effort:** S
- **Touches:** `project`

## Recommendation

**Option A**, chosen with the user. The code and the living spec agree, so the
docstring is the bug. Option B would break configs to protect against almost
nothing.

## Open Questions

None.

## Candidate Capabilities

- `project`: no requirement changes. A doc-only change to `core/config.py`, so
  the change skips delta specs.
