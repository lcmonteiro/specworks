# 8. validate

**Skill**: [/specworks-validate](Skills-Validate). **Writes**: nothing (only the phase
marker). **Boundary**: read-only, even for a one-line fix: it reports, and
points to the phase that owns each problem. Its own reading can add issues but
never overrides a FAIL from the CLI.

| Step | Command | Output used for |
|---|---|---|
| 1. Start | `specworks start validate --change <ref>` | gate review must pass; otherwise FAIL → `/specworks-review` |
| 2. Measurable checks | `specworks validate --change <ref> --json` | `verdict`, `checks[].fix`, `goBackTo` |
| 3. Reading checks | `git diff`, `specworks trace --json` | does each test assert its THEN; does the code follow the design |
| 4. Verdict | — | PASS → `/specworks-close`; FAIL → the earliest phase to go back to |

## A passing report

```console
$ specworks start validate --change add-short-links --base main
...
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0)
add-short-links: phase review → validate
```

**Text**

```console
$ specworks validate --change add-short-links --base main
Completeness (7/7)
  [ok  ] planning artifacts exist (proposal, specs, tasks)
  [ok  ] every task is done (specworks task list --pending)
  [ok  ] every requirement has code (@req tag)
  [ok  ] every acceptance criterion has a test (@ac tag)
  [ok  ] review.md is written
  [ok  ] every finding in review.md is readable (- [ ] R<n> ...)
  [ok  ] no open finding in review.md
Correctness (8/8)
  [ok  ] specs and tasks are valid (specworks check)
  [ok  ] specworks check has no warnings
  [ok  ] the specs are the ones agreed when specify passed
  [ok  ] the test suite passes (commands.test)
           $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:57:25)
  [ok  ] lint passes (commands.lint)
           $ ruff check src tests  (in ., exit 0)
  [ok  ] typecheck passes (commands.typecheck)
  [ok  ] no tag refers to an unknown requirement or criterion
  [ok  ] removed requirements and criteria are gone from tests and code
Coherence (3/3)
  [ok  ] changed files without tags are accounted for in review.md (base main)
  [ok  ] diagram SVGs are up to date (specworks diagrams)
  [ok  ] the change went through review
add-short-links: PASS (0 critical, 0 warnings)
```

**JSON (abridged)**

```json
{
  "name": "add-short-links",
  "verdict": "PASS",
  "critical": 0,
  "warnings": 0,
  "groups": {
    "completeness": { "passed": 7, "total": 7 },
    "correctness": { "passed": 8, "total": 8 },
    "coherence": { "passed": 3, "total": 3 }
  },
  "goBackTo": [],
  "checks": [
    { "name": "planning artifacts exist (proposal, specs, tasks)", "ok": true, "blocking": true, "details": [], "group": "completeness", "fix": "/specworks-specify" },
    { "name": "every task is done (specworks task list --pending)", "ok": true, "blocking": true, "details": [], "group": "completeness", "fix": "/specworks-code" },
    { "name": "every requirement has code (@req tag)", "ok": true, "blocking": true, "details": [], "group": "completeness", "fix": "/specworks-code" }
  ]
}
```

`typecheck` is not configured in this project, so it passes as "not
configured".

## A failing report

With task 2.3 unticked (`specworks task undo 2.3`) and `--no-run`:

**Text**

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

**JSON (failed checks)**

```json
{
  "verdict": "FAIL",
  "critical": 1,
  "warnings": 2,
  "goBackTo": ["/specworks-code"],
  "checks": [
    {
      "name": "every task is done (specworks task list --pending)",
      "ok": false,
      "blocking": true,
      "details": ["2.3 Implement `resolve` (REQ-LINK-002) tagged `@req`; verify the 2.2 tests pass"],
      "group": "completeness",
      "fix": "/specworks-code"
    },
    {
      "name": "the test suite passes (commands.test)",
      "ok": false,
      "blocking": false,
      "details": ["not run (--no-run); run `specworks run test`"],
      "group": "correctness",
      "fix": "/specworks-code"
    }
  ]
}
```

> [!TIP]
> **How the output feeds the skill**
>
> Each failed check carries `fix`, the phase skill that owns it; `goBackTo`
> lists them for the critical ones. The skill reports:
>
>     Validate add-short-links: FAIL
>     CRITICAL  every task is done: 2.3   -> /specworks-code
>
> and suggests the earliest phase: `specworks phase code --change
> add-short-links`, then `/specworks-code add-short-links`. Warnings are listed
> but do not block.

## What the skill checks by reading

The CLI checks what can be measured; the skill re-reads the specs, design.md,
review.md and the diff, and samples each requirement's `@req` code and the
`@ac` tests of its criteria:

- does each test exercise its scenario's WHEN and assert its THEN?
- does the code follow the design decisions, or did review.md record why not?
- is each `accepted` decision in review.md backed by a reason?
- is anything in the diff clearly outside the change's scope?

Each problem is CRITICAL (the spec is not met, or a check is unreliable) or a
WARNING, with the file and the phase that fixes it.
