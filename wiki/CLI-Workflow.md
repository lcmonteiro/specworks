# Gates, review and close

## `specworks gate`

Check whether a change has finished a phase: `specify`, `design`, `test`,
`code`, `review` or `validate`. Exit 1 if a blocking check fails. Every check
of every gate: [Gate checks](Reference-Gates).

```text
specworks gate PHASE --change REF [--no-run] [--base BRANCH] [--allow-open] [--fresh] [--json]
```

| Option | Meaning |
|---|---|
| `--no-run` | design, code, review: do not run the project's commands (reported as a warning) |
| `--base` | review: branch to diff against |
| `--allow-open` | review: open findings do not fail the gate (inside `/specworks-build` they start the next cycle) |
| `--fresh` | run the project's commands even when a result from the same code exists |

**NOT passed**

```console
$ specworks gate test --change add-short-links
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[FAIL] every acceptance criterion has a test (@ac tag)
         AC-LINK-001.3
         AC-LINK-002.2
[FAIL] no tag refers to an unknown requirement or criterion
         AC-LNK-002.2 at tests/test_store.py:28 (no capability uses the prefix LNK; did you mean LINK?)
[ok  ] @ac tags are in test files (configure test_globs if your tests live elsewhere)
[ok  ] removed requirements and criteria are gone from tests and code
gate test: NOT passed
```

**Passed**

```console
$ specworks gate design --change add-short-links
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[ok  ] design.md has an Interfaces section (write "None" when the API does not change)
[ok  ] every file named under Interfaces exists
[ok  ] the existing tests still pass with the stubs (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:56:14)
gate design: passed
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
  "gate": "specify",
  "passed": true,
  "checks": [
    { "name": "specs and tasks are valid (specworks check)", "ok": true, "blocking": true, "details": [] },
    { "name": "specworks check has no warnings", "ok": true, "blocking": false, "details": [] },
    { "name": "tasks.md is written", "ok": true, "blocking": true, "details": [] }
  ]
}
```

**Used by**: every phase skill, as its last step before suggesting the next
phase.

## `specworks run`

Run one of the project's configured commands (`test`, `lint`, `typecheck`,
`build` or `format`) in the module folder that owns the change. The exit code
passes through. It always runs, and records its result for the gates to reuse
([The run cache](Reference-Run-Cache)).

```text
specworks run KEY [--change REF] [--json]
```

**Text**

```console
$ specworks run test --change add-short-links
=========================== short test summary info ============================
FAILED tests/test_store.py::test_ac_link_001_3_non_http_url_is_rejected[https://]
FAILED tests/test_store.py::test_ac_link_001_3_non_http_url_is_rejected[http:///path]
2 failed, 7 passed in 0.02s
```

**JSON**

```json
{
  "key": "test",
  "command": "python -m pytest -q -p no:cacheprovider -o pythonpath=src tests",
  "cwd": ".",
  "exitCode": 0,
  "ok": true,
  "tail": [
    "............                                                             [100%]",
    "12 passed in 0.02s"
  ]
}
```

**Not configured**

```console
$ specworks run typecheck
error: no 'typecheck' command configured; add it under commands: in spec.yml (e.g. test: uv run pytest)
```

**Used by**: [/specworks-adopt](Skills-Adopt) (starting state), [/specworks-design](Skills-Design)
(stubs build, suite green), [/specworks-test](Skills-Test) (red for the right reason),
[/specworks-code](Skills-Code) (green), [/specworks-review](Skills-Review) (after a fix).

## `specworks review`

Drift candidates between a change's specs and its code, in both directions:
requirements without code, criteria without tests, removed IDs still tagged,
unknown tags, and files changed on the branch (git: committed, uncommitted and
untracked, since the base) with no `@req`/`@ac` tag. On the base branch
itself, files changed since the commit before the change started (a warning
when no commit marks that).

```text
specworks review --change REF [--base BRANCH] [--json]
```

**Text**

```console
$ specworks review --change add-short-links --base main
base: main
requirements without code (`@req`): 0
acceptance criteria without a test (`@ac`): 0
removed requirements or criteria still tagged in tests or code: 0
tags to unknown IDs: 0
changed code files without `@req` tags: 1
  src/shortlink/errors.py
changed test files without `@ac` tags: 0
1 drift candidates
```

**JSON**

```json
{
  "name": "add-short-links",
  "ref": "add-short-links",
  "module": "(top)",
  "path": "spec/changes/add-short-links",
  "phase": "review",
  "created": "2026-10-17T19:55:11",
  "skipSpecs": false,
  "base": "main",
  "since": "main",
  "note": "",
  "specErrors": [],
  "findings": {
    "reqWithoutCode": [],
    "acWithoutTests": [],
    "removedStillTagged": [],
    "unknownTags": [],
    "untracedSource": ["src/shortlink/errors.py"],
    "untracedTests": []
  },
  "findingCount": 1,
  "changedFiles": [
    { "path": "src/shortlink/errors.py", "kind": "source", "tags": [] },
    { "path": "src/shortlink/store.py", "kind": "source", "tags": ["REQ-LINK-001", "REQ-LINK-002"] },
    { "path": "tests/test_store.py", "kind": "test", "tags": ["AC-LINK-001.1", "AC-LINK-001.2", "AC-LINK-001.3", "AC-LINK-002.1", "AC-LINK-002.2"] }
  ]
}
```

**Used by**: [/specworks-review](Skills-Review) step 2. Candidates, not verdicts: the
skill reads the code and decides with you.

## `specworks cycle`

After a review: the open findings in `review.md`, the phase each one needs,
and where the next design → test → code → review cycle starts, or that a spec
finding hands over to specify ([Review findings and build cycles](Reference-Findings)).

```text
specworks cycle --change REF [--json]
```

**Next cycle**

```console
$ specworks cycle --change add-short-links
R1 test-gap -> test
next cycle: test -> code -> review
```

**Hand over**

```console
$ specworks cycle --change add-short-links
R1 code-gap -> code
R2 design-gap -> design
R3 spec-gap -> specify
a spec finding: stop the build and run /specworks-specify add-short-links
```

**Done**

```console
$ specworks cycle --change add-short-links
no open findings: the build is done; next is /specworks-validate
```

**JSON**

```json
{
  "name": "add-short-links",
  "ref": "add-short-links",
  "module": "(top)",
  "path": "spec/changes/add-short-links",
  "phase": "review",
  "created": "2026-10-17T19:55:11",
  "skipSpecs": false,
  "reviewed": true,
  "open": [
    { "id": "R1", "type": "test-gap", "text": "**test-gap** AC-LINK-001.3 tests only ...", "phase": "test" }
  ],
  "startAt": "test",
  "phases": ["test", "code", "review"],
  "handOver": null
}
```

**Used by**: [/specworks-build](Skills-Build) (where the next cycle starts),
[/specworks-specify](Skills-Specify) (findings sent back to specify).

## `specworks validate`

The final read-only check before close, in three groups (completeness,
correctness, coherence). Runs the project's test, lint and typecheck commands.
Exit 1 on FAIL. Every check: [Validate checks](Reference-Validate).

```text
specworks validate --change REF [--base BRANCH] [--no-run] [--fresh] [--json]
```

**PASS**

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

**FAIL**

```console
$ specworks validate --change add-short-links --base main --no-run
Completeness (6/7)
  [ok  ] planning artifacts exist (proposal, specs, tasks)
  [FAIL] every task is done (specworks task list --pending)  -> /specworks-code
           2.3 Implement `resolve` (REQ-LINK-002) tagged `@req`; verify the 2.2 tests pass
  ...
add-short-links: FAIL (1 critical, 2 warnings)
go back to: /specworks-code
```

**JSON**

```json
{
  "name": "add-short-links",
  "verdict": "FAIL",
  "critical": 1,
  "warnings": 2,
  "groups": {
    "completeness": { "passed": 6, "total": 7 },
    "correctness": { "passed": 6, "total": 8 },
    "coherence": { "passed": 3, "total": 3 }
  },
  "goBackTo": ["/specworks-code"],
  "checks": [
    {
      "name": "every task is done (specworks task list --pending)",
      "ok": false,
      "blocking": true,
      "details": ["2.3 Implement `resolve` (REQ-LINK-002) tagged `@req`; verify the 2.2 tests pass"],
      "group": "completeness",
      "fix": "/specworks-code"
    }
  ]
}
```

**Used by**: [/specworks-validate](Skills-Validate); `gate validate` (and so `start
close`) runs the same checks.

## `specworks close`

After a passing validate, and only into living specs `check` finds no problem
in: merge the deltas into each living `spec.md` (ADDED appended, MODIFIED
replaced by ID, REMOVED deleted), regenerate `requirements.md` with a History
line, mark the change `done` and move it to `changes/archive/<date>-<name>/`.
Without `--dry-run` it always runs the project's commands for real.

```text
specworks close --change REF [--dry-run] [--no-run] [--base BRANCH] [--json]
```

| Option | Meaning |
|---|---|
| `--dry-run` | show what would be merged and archived; write nothing |
| `--no-run` | with `--dry-run`: validate without running test, lint, typecheck |

**New living spec**

```console
$ specworks close --change add-short-links --base main --dry-run --no-run
would merge links -> src/shortlink/docs/spec.md (new): ADDED REQ-LINK-001, REQ-LINK-002
$ specworks close --change add-short-links --base main
merged links -> src/shortlink/docs/spec.md (new): ADDED REQ-LINK-001, REQ-LINK-002
archived -> spec/changes/archive/2026-10-17-add-short-links
```

**Existing living spec**

```console
$ specworks close --change add-link-expiry --base main --dry-run --no-run
would merge links -> src/shortlink/docs/spec.md: ADDED REQ-LINK-003; MODIFIED REQ-LINK-002
$ specworks close --change add-link-expiry --base main
merged links -> src/shortlink/docs/spec.md: ADDED REQ-LINK-003; MODIFIED REQ-LINK-002
archived -> spec/changes/archive/2026-10-17-add-link-expiry
```

The result: [9. close](Tutorial-Close) and [Change 2: modifying a capability with a living spec](Tutorial-Modify).
**Used by**: [/specworks-close](Skills-Close) (dry run → your go-ahead → real close).
