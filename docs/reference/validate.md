# Validate checks

`specworks validate` (and `gate validate`, `start close`, `close`) run these
checks, in this order. Each has a group and a `fix`: the phase skill that owns
a failure. `verdict` is PASS when no blocking check fails; `goBackTo` lists
the `fix` of every critical failure.

| Group | Check | Blocking | `fix` |
|---|---|:-:|---|
| Completeness | planning artifacts exist (proposal, specs, tasks) | ✔ | `/specworks-specify` |
| Completeness | every task is done | ✔ | `/specworks-code` |
| Completeness | every requirement has code (`@req`) | ✔ | `/specworks-code` |
| Completeness | every acceptance criterion has a test (`@ac`) | ✔ | `/specworks-test` |
| Completeness | `review.md` is written | ✔ | `/specworks-review` |
| Completeness | every finding in `review.md` is readable | ✔ | `/specworks-review` |
| Completeness | no open finding in `review.md` | ✔ | `/specworks-review` |
| Correctness | specs and tasks are valid | ✔ | `/specworks-specify` |
| Correctness | `specworks check` has no warnings | warn | `/specworks-specify` |
| Correctness | the specs are the ones agreed when specify passed | warn | `/specworks-specify` |
| Correctness | the test suite passes | ✔ | `/specworks-code` |
| Correctness | lint passes (passes as "not configured" when absent) | ✔ | `/specworks-code` |
| Correctness | typecheck passes (same) | ✔ | `/specworks-code` |
| Correctness | no tag refers to an unknown ID | ✔ | `/specworks-review` |
| Correctness | removed requirements and criteria are gone | ✔ | `/specworks-code` |
| Coherence | changed files without tags are accounted for | ✔ | `/specworks-review` |
| Coherence | the change's commits are compared with its base | warn | `/specworks-review` |
| Coherence | the tests of each MODIFIED requirement changed with it | warn | `/specworks-test` |
| Coherence | diagram SVGs are up to date | ✔ | `/specworks-specify` |
| Coherence | the change went through review | warn | `/specworks-review` |

Planning artifacts: a change marked with `skip-specs` needs no `specs/`.

## Example

A FAIL with one critical failure and two warnings, and its `goBackTo`:

```console
$ specworks validate --change add-short-links --base main --no-run
Completeness (6/7)
  [ok  ] planning artifacts exist (proposal, specs, tasks)
  [FAIL] every task is done (specworks task list --pending)  -> /specworks-code
           2.3 Implement `resolve` (REQ-LINK-002) tagged `@req`; verify the 2.2 tests pass
  ...
Correctness (6/8)
  ...
  [warn] the test suite passes (commands.test)  -> /specworks-code
           not run (--no-run); run `specworks run test`
  [warn] lint passes (commands.lint)  -> /specworks-code
           not run (--no-run); run `specworks run lint`
  ...
add-short-links: FAIL (1 critical, 2 warnings)
go back to: /specworks-code
```

More in {doc}`../tutorial/validate`.
