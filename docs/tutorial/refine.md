# 1. refine

**Skill**: {doc}`../skills/refine`. **Writes**: `refinement.md` only.
**Boundary**: no requirements, tasks, tests or code, even if you ask to
"build" something.

```{mermaid}
flowchart TD
    A["specworks context --json"] -->|root, capabilities, changes| B{change exists?}
    B -->|no| C["specworks new #lt;name#gt; --json"]
    B -->|yes| D[use it]
    C -->|ref| E[explore code and docs<br/>talk with the user]
    D --> E
    E --> F["specworks instructions refinement --json"]
    F -->|outputPath, template, instruction| G["ask: Ready to record?<br/>write refinement.md"]
    G --> H["specworks status --change ref"]
    H --> I["stop: suggest /specworks-specify"]
```

| Step | Command | Output used for |
|---|---|---|
| 1. Check the project | `specworks context --json` | see {doc}`setup` |
| 2. Create the change | `specworks new add-short-links --json` | `ref`, for every later command |
| 3. Explore | (reads code, asks one question at a time) | problem, scope, constraints, options |
| 4. Write `refinement.md` | `specworks instructions refinement --change <ref> --json` | `outputPath`, `template`, `instruction`, `exists` |
| 5. Show the result | `specworks status --change <ref>` | summary; then stop |

## Create the change

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
```

It creates `spec/changes/add-short-links/.change.yaml`:

```yaml
name: add-short-links
created: '2026-10-17T19:55:11'
phase: refine
```

## Ask for the instructions

Long strings abridged:

```console
$ specworks instructions refinement --change add-short-links --json
{
  "artifact": "refinement",
  "phase": "refine",
  "change": "add-short-links",
  "module": "(top)",
  "root": "/work/shortlink",
  "changeDir": "spec/changes/add-short-links",
  "outputPath": "spec/changes/add-short-links/refinement.md",
  "exists": false,
  "optional": true,
  "context": "Python 3.12 library, standard library only. ...",
  "instruction": "Capture the shared understanding of the problem BEFORE committing to a solution.\nThis is the input for the proposal; it is not a plan.\n\nSections:\n- **Problem**: 2-4 sentences. ...",
  "template": "# Refinement: <!-- change name -->\n\n## Problem\n\n<!-- What hurts, for whom, and why now -->\n\n## Context\n\n**Observed:** ...",
  "dependencies": []
}
```

```{admonition} How the output feeds the skill
:class: tip feeds

`template` gives the headings, `instruction` the rules for each section
(Problem in 2-4 sentences, Observed vs Assumed, 2-3 real options with effort
and capabilities touched, a Recommendation or "Pending"), `outputPath` the
file to write. `exists: false` means "create"; `true` would mean "re-read it
and update it; do not overwrite the user's edits". The full instruction and
template: {doc}`../reference/artifacts`.
```

## Write `refinement.md`

After the conversation, and after asking "Ready to record the refinement?"
(agreeing to answers during the discussion is not permission to write):

```{literalinclude} ../example/shortlink/spec/changes/archive/2026-10-17-add-short-links/refinement.md
:language: markdown
:caption: spec/changes/add-short-links/refinement.md
```

## Show the result and stop

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

```{admonition} How the output feeds the skill
:class: tip feeds

`refinement.md` is `done`, which makes `proposal.md` `ready`: the next
artifact belongs to specify. The skill summarises the problem, options and
recommendation, and ends with "When you are ready, run `/specworks-specify
add-short-links`."
```

```{note}
The open question "Should codes expire?" is the seed of change 2
({doc}`modify`).
```
