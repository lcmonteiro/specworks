# Specs, tasks and diagrams

## `specworks spec list` / `spec show`

Read capabilities and their living specs. `spec show` gives one capability's
requirements, its ID prefix, the **next free ID** (counting the living spec,
the History of removed IDs, and other changes in flight) and the delta path;
it also works for a capability that is new in a change.

```text
specworks spec list [--json]
specworks spec show REF [--no-scenarios] [--json]
```

**spec list**

```console
$ specworks spec list
links                        REQ-LINK-  3 req  src/shortlink/docs/spec.md
```

```json
{
  "root": "/work/shortlink",
  "capabilities": [
    {
      "ref": "links", "module": "(top)", "name": "links", "new": false,
      "prefix": "LINK", "nextId": "REQ-LINK-004", "deltaPath": "specs/links/spec.md",
      "codePath": "src/shortlink", "livingSpec": "src/shortlink/docs/spec.md",
      "hasSpec": true, "purpose": "Turn long URLs into short codes and resolve the codes back.",
      "requirements": 3
    }
  ]
}
```

**spec show**

```console
$ specworks spec show links
links
  prefix:    REQ-LINK-  next: REQ-LINK-003
  delta:     specs/links/spec.md
  living:    src/shortlink/docs/spec.md
  REQ-LINK-001  Shorten a URL
  REQ-LINK-002  Resolve a code
```

**spec show --json**

```json
{
  "ref": "links",
  "module": "(top)",
  "name": "links",
  "new": false,
  "prefix": "LINK",
  "nextId": "REQ-LINK-003",
  "deltaPath": "specs/links/spec.md",
  "codePath": "src/shortlink",
  "livingSpec": "src/shortlink/docs/spec.md",
  "hasSpec": true,
  "purpose": "Turn long URLs into short codes and resolve the codes back.",
  "requirements": [
    {
      "id": "REQ-LINK-001",
      "title": "Shorten a URL",
      "scenarios": [
        {
          "id": "AC-LINK-001.1",
          "title": "A valid URL gets a code",
          "text": "- **WHEN** `shorten(\"https://example.com/a\")` is called\n- **THEN** it returns a 6-character code of letters and digits"
        }
      ]
    }
  ]
}
```

| Field | Read by the skill to |
|---|---|
| `prefix`, `nextId` | number new requirements |
| `deltaPath` | place the delta spec: `<changeDir>/<deltaPath>` |
| `codePath` | find the code and tests to read and imitate |
| `livingSpec`, `hasSpec`, `purpose` | know whether the delta needs `## Purpose` (new spec) |
| `requirements[].scenarios[].text` | copy a whole block for MODIFIED |
| `new` | a capability that a change creates and that is not registered yet (close registers it) |

## `specworks capability add`

Register a capability in a module's config. Required before closing a change
that creates it.

```text
specworks capability add NAME --path DIR [--module MODULE] [--prefix PREFIX] [--description TEXT] [--json]
```

| Option | Meaning |
|---|---|
| `--path` | code folder that owns it, relative to the module root (required) |
| `--module` | module that owns it (default: the current one) |
| `--prefix` | requirement ID prefix (default: derived from the name) |
| `--description` | one line on what it covers |

```console
$ specworks capability add links --path src/shortlink --prefix LINK --description "Create short codes for URLs and resolve them"
registered links -> src/shortlink (REQ-LINK-)
$ specworks capability add links2 --path src/x --prefix LINK
error: the ID prefix LINK is already used by links; choose another with --prefix
```

With `--json` it prints the new capability as `spec show --json` does.

## `specworks instructions`

Template, rules and output path for writing one artifact of a change:
`refinement`, `proposal`, `specs`, `design`, `tasks`, `traceability` or
`review`.

```text
specworks instructions ARTIFACT --change REF [--json]
```

```json
{
  "artifact": "specs",
  "phase": "specify",
  "change": "add-short-links",
  "module": "(top)",
  "root": "/work/shortlink",
  "changeDir": "spec/changes/add-short-links",
  "outputPath": "spec/changes/add-short-links/specs/**/spec.md",
  "exists": false,
  "optional": false,
  "context": "Python 3.12 library, standard library only. ...",
  "instruction": "Write one delta spec per capability listed in the proposal: ...",
  "template": "# Spec Delta: <!-- capability ref -->\n\n## Purpose\n...",
  "dependencies": [
    { "id": "proposal", "path": "spec/changes/add-short-links/proposal.md", "done": false }
  ],
  "capabilities": [ { "ref": "links", "prefix": "LINK", "nextId": "REQ-LINK-001", "deltaPath": "specs/links/spec.md", "...": "..." } ],
  "writtenDeltas": []
}
```

Every instruction and template: [Artifacts: instructions and templates](Reference-Artifacts). **Used by**:
every skill that writes an artifact.

## `specworks check`

Check a change's proposal, delta specs and tasks: IDs, SHALL/MUST, scenarios,
MODIFIED/REMOVED targets, ID clashes with other changes, task format and
coverage. Warns about a new capability not registered yet, a MODIFIED block
that drops criteria, a requirement another close modified since this change
started, and a broken living spec.

- **ID clashes**: the same ID ADDED by two active changes, or one requirement
  MODIFIED or REMOVED by two of them. The clash is an error in the change that
  started later and a warning in the earlier one, which can still close.
- **A broken living spec**: in a capability the change touches, an ID used
  twice, a requirement or criterion without an ID, a requirement without a
  scenario or without SHALL/MUST. `close` refuses to merge into one.

```text
specworks check --change REF [--strict] [--json]
```

| Option | Meaning |
|---|---|
| `--strict` | warnings are errors (exit 1) |

**Errors**

```console
$ specworks check --change add-short-links
error   spec/changes/add-short-links/specs/links/spec.md:9: REQ-LINK-001: state the requirement with SHALL or MUST
error   spec/changes/add-short-links/specs/links/spec.md:22: AC-LINK-001.2 is under REQ-LINK-002; number it AC-LINK-002.<n>
warning spec/changes/add-short-links/tasks.md: tasks.md is not written yet
add-short-links: INVALID (2 errors, 1 warnings)
```

**Warning**

```console
$ specworks check --change add-link-expiry
warning spec/changes/add-link-expiry/specs/links/spec.md:22: REQ-LINK-002: this MODIFIED block drops AC-LINK-002.2; copy the whole block from the living spec, or drop a criterion only on purpose (with its tests)
add-link-expiry: valid (0 errors, 1 warnings)
```

**--strict**

```console
$ specworks check --change add-qr-codes --strict
warning spec/changes/add-qr-codes/tasks.md: tasks.md is not written yet
add-qr-codes: INVALID (0 errors, 1 warnings)
```

**JSON**

```json
{
  "name": "add-qr-codes",
  "ref": "add-qr-codes",
  "module": "(top)",
  "path": "spec/changes/add-qr-codes",
  "phase": "specify",
  "created": "2026-10-17T21:00:45",
  "skipSpecs": false,
  "valid": true,
  "errors": 0,
  "warnings": 1,
  "issues": [
    {
      "level": "warning",
      "file": "spec/changes/add-qr-codes/tasks.md",
      "line": 0,
      "message": "tasks.md is not written yet"
    }
  ]
}
```

Every gate and validate run the same checks ("specs and tasks are valid";
warnings as "specworks check has no warnings").

## `specworks trace`

The requirement → acceptance criterion → task → test (`@ac`) → code (`@req`)
matrix of a change, and its gaps. `--write` saves it as `traceability.md`.

```text
specworks trace --change REF [--write] [--json]
```

**Text**

```console
$ specworks trace --change add-qr-codes
# Traceability: add-qr-codes

Generated by `specworks trace --write`; do not edit by hand.

| Capability | Requirement | Acceptance criterion | Tasks | Tests | Code |
|---|---|---|---|---|---|
| qr | REQ-QR-001 Render a QR code (ADDED) | AC-QR-001.1 A code becomes an SVG | 1.1, 1.2 | — | — |

## Gaps

- Acceptance criteria without a test (`@ac`): AC-QR-001.1
- Requirements without code (`@req`): REQ-QR-001
```

**JSON (one row)**

```json
{
  "capability": "links",
  "req": "REQ-LINK-001",
  "title": "Shorten a URL",
  "section": "ADDED",
  "ac": "AC-LINK-001.1",
  "ac_title": "A valid URL gets a code",
  "tasks": ["1.1", "1.2", "1.3"],
  "tests": ["tests/test_store.py:9"],
  "code": []
}
```

**Used by**: [/specworks-specify](Skills-Specify) (`--write`), [/specworks-test](Skills-Test) (tests
of MODIFIED criteria), [/specworks-code](Skills-Code) (where stubs and tests are),
[/specworks-validate](Skills-Validate) (sampling).

## `specworks task list` / `done` / `undo`

List the tasks of a change with their IDs, and tick or untick checkboxes
without touching the rest of `tasks.md`.

```text
specworks task list --change REF [--pending] [--json]
specworks task done N.M [N.M ...] --change REF [--json]
specworks task undo N.M [N.M ...] --change REF [--json]
```

**list**

```console
$ specworks task list --change add-qr-codes
[ ] 1.1 Add `qr_svg` as a stub (REQ-QR-001); verify the existing tests pass
[x] 1.2 Write a failing test for AC-QR-001.1 tagged `@ac`; verify it fails
1/2 done
```

**undo**

```console
$ specworks task undo 1.2 --change add-qr-codes
[ ] 1.1 Add `qr_svg` as a stub (REQ-QR-001); verify the existing tests pass
[ ] 1.2 Write a failing test for AC-QR-001.1 tagged `@ac`; verify it fails
0/2 done
```

**JSON**

```json
{
  "name": "add-qr-codes",
  "ref": "add-qr-codes",
  "module": "(top)",
  "path": "spec/changes/add-qr-codes",
  "phase": "specify",
  "created": "2026-10-17T21:00:45",
  "skipSpecs": false,
  "done": 0,
  "total": 2,
  "tasks": [
    { "num": "1.1", "text": "Add `qr_svg` as a stub (REQ-QR-001); verify the existing tests pass", "done": false, "line": 5, "ids": ["REQ-QR-001"] },
    { "num": "1.2", "text": "Write a failing test for AC-QR-001.1 tagged `@ac`; verify it fails", "done": false, "line": 6, "ids": ["AC-QR-001.1"] }
  ]
}
```

**Used by**: [/specworks-design](Skills-Design), [/specworks-test](Skills-Test) and
[/specworks-code](Skills-Code) tick their tasks once each one's verification passed.

## `specworks diagrams`

Render the D2 diagrams (`diagrams/*.d2`) of a change, or of a docs folder, to
SVG with the workspace's theme. Each SVG is stamped with a hash of its source
and the settings, so an outdated one is detected.

```text
specworks diagrams (--change REF | --dir FOLDER) [--check] [--force] [--json]
specworks diagrams --themes
```

| Option | Meaning |
|---|---|
| `--change` / `--dir` | the change's `diagrams/`, or `<FOLDER>/diagrams/` (e.g. a capability's living docs) |
| `--check` | only report missing or outdated SVGs (exit 1 if any); needs no `d2` |
| `--force` | re-render every diagram, even up-to-date ones |
| `--themes` | list the themes and the one in use |

**Render**

```console
$ specworks diagrams --change add-short-links
rendered  spec/changes/add-short-links/diagrams/shorten-flow.svg
```

**--check**

```console
$ specworks diagrams --check --change add-qr-codes
missing   spec/changes/add-qr-codes/diagrams/flow.svg
$ specworks diagrams --change add-qr-codes
rendered  spec/changes/add-qr-codes/diagrams/flow.svg
$ # ... flow.d2 edited ...
$ specworks diagrams --check --change add-qr-codes
stale     spec/changes/add-qr-codes/diagrams/flow.svg
```

**D2 error**

```console
$ specworks diagrams --change add-qr-codes
error     spec/changes/add-qr-codes/diagrams/flow.svg
          d2 failed on flow.d2: /work/shortlink/spec/changes/add-qr-codes/diagrams/flow.d2:1:6: maps must be terminated with }
```

**--themes**

```console
$ specworks diagrams --themes
in use: theme neutral-default, dark_theme dark-mauve  (spec.yml)
d2:     .../site-packages/pyd2/bin/d2 (pyd2)
     0  neutral-default
     1  neutral-grey
     3  flagship-terrastruct
     4  cool-classics
     5  mixed-berry-blue
     6  grape-soda
     7  aubergine
     8  colorblind-clear
   100  vanilla-nitro-cola
   101  orange-creamsicle
   102  shirley-temple
   103  earth-tones
   104  everglade-green
   105  buttered-toast
   300  terminal
   301  terminal-grayscale
   302  origami
   303  c4
   200  dark-mauve  (dark)
   201  dark-flagship-terrastruct  (dark)
```

**Used by**: [/specworks-specify](Skills-Specify) (change diagrams),
[/specworks-close](Skills-Close) (`--dir <docsPath>`). Validate fails while an SVG is
missing or outdated.
