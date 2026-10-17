# Artifacts: instructions and templates

Each artifact of a change has an `instruction` (the rules the agent follows)
and a `template` (its structure). `specworks instructions <artifact> --change
<ref> --json` returns both; they come from the files below, which are part of
the installed package.

| Artifact | Phase | File | Requires | Optional |
|---|---|---|---|---|
| `refinement` | refine | `refinement.md` | — | yes |
| `proposal` | specify | `proposal.md` | refinement | |
| `specs` | specify | `specs/**/spec.md` | proposal | |
| `design` | specify | `design.md` | proposal | yes |
| `tasks` | specify | `tasks.md` | specs, design | |
| `traceability` | specify | `traceability.md` (generated) | tasks | |
| `review` | review | `review.md` | tasks | |

## The rules: `schema.yaml`

````{dropdown} src/specworks/schema.yaml
:icon: code
:open:

```{literalinclude} ../../src/specworks/schema.yaml
:language: yaml
```
````

## The templates

````{dropdown} refinement.md
:icon: file

```{literalinclude} ../../src/specworks/templates/refinement.md
:language: markdown
```
````

````{dropdown} proposal.md
:icon: file

```{literalinclude} ../../src/specworks/templates/proposal.md
:language: markdown
```
````

````{dropdown} spec.md (delta spec)
:icon: file

```{literalinclude} ../../src/specworks/templates/spec.md
:language: markdown
```
````

````{dropdown} design.md
:icon: file

```{literalinclude} ../../src/specworks/templates/design.md
:language: markdown
```
````

````{dropdown} tasks.md
:icon: file

```{literalinclude} ../../src/specworks/templates/tasks.md
:language: markdown
```
````

````{dropdown} review.md
:icon: file

```{literalinclude} ../../src/specworks/templates/review.md
:language: markdown
```
````

Filled-in examples of every one of them are in the tutorial:
{doc}`../tutorial/refine`, {doc}`../tutorial/specify`,
{doc}`../tutorial/design`, {doc}`../tutorial/build-cycle`.
