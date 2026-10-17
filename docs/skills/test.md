# /specworks-test

:Phase: test
:Writes: tests tagged `@ac <AC-ID>`
:Next: `/specworks-code <ref>`
:Example: {doc}`../tutorial/test`

Turn every acceptance criterion into at least one test, written against the
stubs, that **fails for the right reason**: not implemented yet, never an
import or syntax error. Use it when a change has its interfaces, or when you
say "write the acceptance tests" or "specworks test".

## Steps

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 1 | Start the phase | `specworks start test --change <ref>` | gates left behind (design, and specify if skipped); exit 1 → `/specworks-design` or `/specworks-specify`. `commands.test` from the context (if empty: find it, confirm it, suggest adding it) |
| 2 | Load the plan and conventions | `specworks task list --pending`; `specworks spec show <ref> --json`; `specworks trace --change <ref> --json` | ADDED, MODIFIED and REMOVED criteria; `codePath` (existing tests to imitate); `rows[].tests` of MODIFIED/REMOVED criteria (tests to update or delete) |
| 3 | Check the API covers every criterion | — | a missing parameter, error type or field → back to `/specworks-design` |
| 4 | Write the tests, one criterion at a time | — | GIVEN → arrange, WHEN → act, THEN → assert, through the public API |
| 5 | Run them | `specworks run test --change <ref>` | every new test fails; on the stub, not an import/collection error; existing tests still pass |
| 6 | Tick, gate, trace | `specworks task done <N.M>`; `specworks gate test`; `specworks trace --write` | untested criteria and unknown tags to fix |
| 7 | Report and stop | — | table: criterion, test, why it fails; "run `/specworks-code <ref>`" |

## Tagging and naming

```python
# @ac AC-AUTH-003.2
def test_ac_auth_003_2_expired_link_is_rejected(): ...
```

```typescript
// @ac AC-AUTH-003.2
it("AC-AUTH-003.2 rejects an expired link", ...)
```

One test may carry several criteria (`# @ac AC-AUTH-003.1, AC-AUTH-003.2`)
when it truly checks all of them. MODIFIED criteria: update the existing
tests, keeping their tags. REMOVED requirements, and criteria a MODIFIED block
leaves out: delete their tests and say which.

## Reading the test run

| Result | Meaning | What the skill does |
|---|---|---|
| new test fails on `NotImplementedError` / assertion | right reason | continue |
| `ImportError`, collection or syntax error | a bug in the test or stub | fix it now |
| a new test already passes | it checks nothing new, or the behaviour exists | strengthen it or tell you |
| an existing test fails | a stub or test broke something | fix it |

## Guardrails

- No implementation and no new interfaces.
- Tests verify the criteria as written; a wrong or untestable criterion goes
  back to `/specworks-specify`.
- Never skips, disables, marks as expected-to-fail or loosens a test to get
  the right colour.

## Source

````{dropdown} specworks-test/SKILL.md
:icon: code

```{literalinclude} ../../src/specworks/skills/specworks-test/SKILL.md
:language: markdown
```
````
