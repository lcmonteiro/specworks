# /specworks-validate

:Phase: validate
:Writes: nothing (only the phase marker)
:Next: `/specworks-close <ref>` on PASS; the earliest phase to go back to on FAIL
:Example: {doc}`../tutorial/validate`

A final, read-only pass/fail check that the change is complete, correct and
coherent, with every failure pointing to the phase that fixes it. Use it when
a change has been reviewed, or when you say "validate the change" or "is the
change ready to close".

## Steps

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 1 | Start the phase | `specworks start validate --change <ref> [--base <branch>]` | `gate review` (and earlier gates left behind); exit 1 → verdict FAIL, suggest the failed gate's skill, stop |
| 2 | Measurable checks | `specworks validate --change <ref> --json` | `verdict`; per check `ok`, `blocking`, `group`, `fix`; `goBackTo` |
| 3 | Reading checks (read-only) | `git diff <base>...HEAD`; `specworks trace --change <ref> --json` | sampled `@req` code and `@ac` tests per requirement |
| 4 | Verdict and stop | — | PASS → "run `/specworks-close <ref>`"; FAIL → critical issues grouped by phase, earliest one suggested |

## The report

```text
Validate <ref>: PASS | FAIL

Completeness  5/5   Correctness  6/6   Coherence  3/3
CRITICAL  every requirement has code: REQ-AUTH-002   -> /specworks-code
WARNING   AC-AUTH-003.2 test checks the status only  -> /specworks-review
```

- **Completeness**: planning artifacts exist, every task done, every
  requirement has `@req` code, every criterion an `@ac` test, review done.
- **Correctness**: specs valid; tests, lint and typecheck pass; no unknown
  tags; removed requirements gone.
- **Coherence**: untagged changed files accounted for; diagrams up to date;
  the change went through review.

Every check, with its group and `fix`: {doc}`../reference/validate`.

## Guardrails

- Never modifies the project, not even a one-line fix: a fix here would skip
  the review and the records the other phases keep.
- A FAIL from `specworks validate` is never overridden; the skill's reading
  can only add issues.
- Every issue names the check or file and the phase that fixes it; taste is
  not reported.

## Source

````{dropdown} specworks-validate/SKILL.md
:icon: code

```{literalinclude} ../../src/specworks/skills/specworks-validate/SKILL.md
:language: markdown
```
````
