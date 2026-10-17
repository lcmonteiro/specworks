# /specworks-review

:Phase: review
:Writes: `review.md`; small, local, agreed fixes to code, tests, delta specs and design.md
:Next: `/specworks-validate <ref>`, or the phase a finding is sent back to
:Example: {doc}`../tutorial/review`

Make the code, the specs and the design (API) say the same thing. For each
difference, decide which one is right and propose the change to the others.
Use it after the code phase, or when you say "review the change", "sync code
and spec", "check for drift" or "specworks review".

## Steps

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 1 | Start the phase | `specworks start review --change <ref>` | `gate code` (its test run is reused when the code did not change); exit 1 → `/specworks-code` |
| 2 | Collect drift candidates | `specworks review --change <ref> --json [--base <branch>]` | spec → code: `reqWithoutCode`, `acWithoutTests`, `removedStillTagged`, `unknownTags`; code → spec: `untracedSource`, `untracedTests` |
| 3 | Read the diff in both directions | `git diff <base>...HEAD`, `git status` | does tagged code do exactly what each requirement says; is every new behaviour covered; would each test fail if the behaviour broke; tags; Interfaces and Decisions; security, data loss, error handling |
| 4 | Propose a change per finding, decide with you | `specworks run test`, `specworks check`, `specworks spec show <cap> --json` (for a small fix here) or `specworks phase <phase>` (to send it back) | — |
| 5 | Write `review.md` | `specworks instructions review --change <ref> --json` | template and rules |
| 6 | Gate and trace | `specworks gate review [--allow-open]`; `specworks trace --write` | open findings, unknown types, unaccounted files, a red suite |
| 7 | Report and stop | — | findings by type and decision; what changed; anything sent back |

## Fix here, or send back

| Change to | Here (small, local) | Back to (larger) |
|---|---|---|
| **code** | fix code and tests, `specworks run test` | `/specworks-code`: a requirement is far from done |
| **spec** | edit the delta spec (ADDED with the next free ID, MODIFIED with the whole block), add its test, tag and task, `specworks check` | `/specworks-specify`: several requirements, a new capability, or the scope changes |
| **design / API** | one interface, no other callers: update Interfaces (or the Decision), code and tests together | `/specworks-design`: the API changes for other callers or several interfaces |

To send it back: record the finding open with the agreed proposal
(`back to <phase>: ...`), then `specworks phase <phase> --change <ref>`.
`accepted: <reason>` closes a finding without a change, only with your
explicit agreement.

## Inside `/specworks-build`

No fixes are applied here. Every finding that needs work is recorded open with
`back to <specify|design|test|code>: ...`, and the gate runs with
`--allow-open`; `specworks cycle` turns the open findings into the next cycle
({doc}`build`).

## `review.md`

```markdown
## Findings

- [x] R1 **test-gap** <what drifts, with IDs> (`file:line`)
  - **Decision**: <code fixed | spec updated | design updated | back to <phase>: ... | accepted: reason>

## Changed files without tags

- `src/shortlink/errors.py`: error types only, used by the tagged `shorten` (REQ-LINK-001)
```

Finding types and how they route: {doc}`../reference/findings`.

## Guardrails

- Never changes a spec or an API silently: every update and every accepted
  difference is agreed with you and recorded.
- Fixes drift; does not add features (those are candidates for a new change).
- Never weakens tests or deletes failing ones.
- Keeps IDs stable: changed behaviour is a MODIFIED requirement with the same ID.

## Source

````{dropdown} specworks-review/SKILL.md
:icon: code

```{literalinclude} ../../src/specworks/skills/specworks-review/SKILL.md
:language: markdown
```
````
