# Other lifecycle commands

## Names are never reused

`requirements.md`'s History refers to a change by name, so an archived name
stays taken:

```console
$ specworks new add-short-links
error: change 'add-short-links' was archived at spec/changes/archive/2026-10-17-add-short-links; requirements.md History refers to it by name, so pick another one
```

## A change with no behaviour change

A refactor, tooling or docs change has no delta specs. It is marked instead of
being given an invented requirement:

```console
$ specworks list
add-custom-codes                 refine
tidy-store-internals             refine
$ specworks skip-specs --change tidy-store-internals
tidy-store-internals: skips delta specs
```

```console
$ specworks status --change tidy-store-internals --json
{
  "name": "tidy-store-internals",
  "skipSpecs": true,
  "artifacts": [
    { "id": "refinement", "status": "ready", ... },
    { "id": "proposal", "status": "ready", ... },
    { "id": "specs", "status": "skipped", ... },
    { "id": "design", "status": "blocked", ... },
    { "id": "tasks", "status": "ready", ... },
    ...
  ]
}
```

`specworks skip-specs --off` undoes it.

## Dropping a change

`abandon` archives a change without merging anything; it keeps the phase and
the reason:

```console
$ specworks abandon --change add-custom-codes --reason "product dropped vanity codes"
add-custom-codes: abandoned in phase refine, archived at spec/changes/archive/2026-10-17-add-custom-codes
$ specworks list --archived
add-custom-codes                 2026-10-17  abandoned in refine: product dropped vanity codes
add-link-expiry                  2026-10-17  closed
add-short-links                  2026-10-17  closed
```

```{literalinclude} ../example/shortlink/spec/changes/archive/2026-10-17-add-custom-codes/.change.yaml
:language: yaml
:caption: archive/2026-10-17-add-custom-codes/.change.yaml
```

`specworks status` also reads an archived change, by name or by
`<date>-<name>`; its JSON then has `"archived": true`.

## The phase marker by hand

`specworks phase` moves a change without checks, except to `done`:

```console
$ specworks phase done --change tidy-store-internals
error: a change becomes done only through `specworks close`, which merges its specs and archives it
$ specworks start done --change tidy-store-internals
error: cannot start 'done'; phases are refine, specify, design, test, code, review, validate, close (`specworks close` finishes a change)
```
