# Changes and phases

## `specworks new`

Create a change folder (phase `refine`) in the current module, or in
`--module`.

```text
specworks new NAME [--module MODULE] [--json]
```

The name is kebab-case. `archive` is reserved, and the name of a closed or
abandoned change stays taken.

```console
$ specworks new add-short-links --json
{
  "name": "add-short-links",
  "ref": "add-short-links",
  "module": "(top)",
  "path": "spec/changes/add-short-links",
  "phase": "refine",
  "created": "2026-10-17T19:55:11",
  "skipSpecs": false
}
$ specworks new add-short-links
error: change 'add-short-links' was archived at spec/changes/archive/2026-10-17-add-short-links; requirements.md History refers to it by name, so pick another one
```

**Used by**: [/specworks-refine](Skills-Refine), [/specworks-specify](Skills-Specify) (when no change
fits), [/specworks-adopt](Skills-Adopt) (baseline). The skill uses `ref` in every later
command.

## `specworks list`

Active changes of the current module, or all modules with `--all`; closed and
abandoned ones with `--archived`. A leftover copy of an active change that is
also archived is flagged.

```text
specworks list [--all] [--archived] [--json]
```

```console
$ specworks list
add-custom-codes                 refine
tidy-store-internals             refine
$ specworks list --archived
add-custom-codes                 2026-10-17  abandoned in refine: product dropped vanity codes
add-link-expiry                  2026-10-17  closed
add-short-links                  2026-10-17  closed
```

## `specworks status`

Phase and artifact states (`done`, `ready`, `blocked`, `skipped`) of a change,
active or archived.

```text
specworks status --change REF [--json]
```

**Text**

```console
$ specworks status --change add-short-links
add-short-links (phase: refine)
  [ done  ] refinement.md
  [ ready ] proposal.md
  [blocked] specs/**/spec.md
  [blocked] design.md
  [blocked] tasks.md
  [blocked] traceability.md
  [blocked] review.md
```

**JSON (abridged)**

```json
{
  "name": "tidy-store-internals",
  "ref": "tidy-store-internals",
  "module": "(top)",
  "path": "spec/changes/tidy-store-internals",
  "phase": "refine",
  "created": "2026-10-17T19:58:47",
  "skipSpecs": true,
  "phases": ["refine", "specify", "design", "test", "code", "review", "validate", "close", "done"],
  "artifacts": [
    { "id": "refinement", "phase": "refine", "generates": "refinement.md", "status": "ready", "requires": [], "optional": true },
    { "id": "proposal", "phase": "specify", "generates": "proposal.md", "status": "ready", "requires": ["refinement"], "optional": false },
    { "id": "specs", "phase": "specify", "generates": "specs/**/spec.md", "status": "skipped", "requires": ["proposal"], "optional": false },
    { "id": "design", "phase": "specify", "generates": "design.md", "status": "blocked", "requires": ["proposal"], "optional": true },
    { "id": "tasks", "phase": "specify", "generates": "tasks.md", "status": "ready", "requires": ["specs", "design"], "optional": false },
    { "id": "traceability", "phase": "specify", "generates": "traceability.md", "status": "blocked", "requires": ["tasks"], "optional": false },
    { "id": "review", "phase": "review", "generates": "review.md", "status": "blocked", "requires": ["tasks"], "optional": false }
  ]
}
```

**Archived**

```console
$ specworks status --change add-short-links
add-short-links (phase: done), archived at spec/changes/archive/2026-10-17-add-short-links
  [ done  ] refinement.md
  [ done  ] proposal.md
  [ done  ] specs/**/spec.md
  [ done  ] design.md
  [ done  ] tasks.md
  [ done  ] traceability.md
  [ done  ] review.md
```

Its JSON has `"archived": true` and the archive `path`.

**Used by**: [/specworks-refine](Skills-Refine) and [/specworks-specify](Skills-Specify) (report),
[/specworks-specify](Skills-Specify) and [/specworks-build](Skills-Build) (which artifacts to re-read).

## `specworks phase`

Move a change to another phase, **unchecked**. `done` is refused: only
`specworks close` sets it.

```text
specworks phase TO --change REF [--json]
```

```console
$ specworks phase specify --change add-short-links
add-short-links: phase → specify
$ specworks phase done --change tidy-store-internals
error: a change becomes done only through `specworks close`, which merges its specs and archives it
```

**Used by**: [/specworks-specify](Skills-Specify) (enter specify), [/specworks-review](Skills-Review)
(send a change back), [/specworks-validate](Skills-Validate) (suggest going back).

## `specworks start`

Move a change to a phase **once the gates it depends on pass**; exit 1 and the
phase unchanged if one fails. Moving forward, every phase left behind must
pass its gate; going back or re-entering needs the gate of the phase just
before ([What `start` checks](Reference-Start-Rules)). Passing `gate specify` records the
requirements' fingerprints in `.change.yaml`.

```text
specworks start PHASE --change REF [--no-run] [--base BRANCH] [--fresh] [--json]
```

**Blocked**

```console
$ specworks start test --change add-short-links
gate specify:
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] tasks.md is written
gate design:
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[FAIL] design.md has an Interfaces section (write "None" when the API does not change)
         write the agreed API under ## Interfaces in design.md (specworks instructions design)
[ok  ] every file named under Interfaces exists
[ok  ] the existing tests still pass with the stubs (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0)
add-short-links: stays in specify; gate design NOT passed
```

**Passed**

```console
$ specworks start design --change add-short-links
gate specify:
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] tasks.md is written
add-short-links: phase specify → design
```

**JSON**

```json
{
  "name": "add-qr-codes",
  "ref": "add-qr-codes",
  "module": "(top)",
  "path": "spec/changes/add-qr-codes",
  "phase": "design",
  "created": "2026-10-17T21:00:45",
  "skipSpecs": false,
  "from": "specify",
  "started": true,
  "gates": [
    {
      "gate": "specify",
      "passed": true,
      "checks": [
        { "name": "specs and tasks are valid (specworks check)", "ok": true, "blocking": true, "details": [] },
        { "name": "specworks check has no warnings", "ok": true, "blocking": false, "details": [] },
        { "name": "tasks.md is written", "ok": true, "blocking": true, "details": [] }
      ]
    }
  ]
}
```

```console
$ specworks start done --change tidy-store-internals
error: cannot start 'done'; phases are refine, specify, design, test, code, review, validate, close (`specworks close` finishes a change)
```

**Used by**: every phase skill from design on, as its first step.

## `specworks skip-specs`

Mark a change with no behaviour change (refactor, tooling, docs): it needs no
delta specs. `--off` requires them again.

```text
specworks skip-specs --change REF [--off] [--json]
```

```console
$ specworks skip-specs --change tidy-store-internals
tidy-store-internals: skips delta specs
```

`status` then shows `specs` as `skipped`. **Used by**:
[/specworks-specify](Skills-Specify), instead of inventing a requirement.

## `specworks abandon`

Archive a change without merging anything. It keeps its phase and records why;
its name stays taken.

```text
specworks abandon --change REF --reason TEXT [--json]
```

```console
$ specworks abandon --change add-custom-codes --reason "product dropped vanity codes"
add-custom-codes: abandoned in phase refine, archived at spec/changes/archive/2026-10-17-add-custom-codes
```

```yaml
# spec/changes/archive/2026-10-17-add-custom-codes/.change.yaml
name: add-custom-codes
created: '2026-10-17T19:58:47'
phase: refine
abandoned: product dropped vanity codes
```
