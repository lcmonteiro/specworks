# How a command's output feeds the skill

A skill reads the result of every `specworks` command through three channels,
and each one drives a decision.

## 1. The exit code

`check`, `gate`, `start`, `validate`, `close` and `diagrams --check` exit `1`
when something blocks; `run` passes the project command's own exit code
through. Every skill branches on it. From `/specworks-design`:

> It runs `gate specify` and moves the change to design only if it passes.
> If it fails, stop: show the failing checks and suggest
> `/specworks-specify <ref>` to finish the plan.

## 2. Check lines

Gates and validate print one line per check, with indented details:

```text
[ok  ] every requirement has code (@req tag)
[FAIL] every acceptance criterion has a test (@ac tag)
         AC-LINK-001.3
         AC-LINK-002.2
[warn] the specs are the ones agreed when specify passed
         REQ-LINK-002 changed
```

`[ok  ]`
: the check passed.

`[FAIL]`
: a **blocking** check failed: the gate fails (exit 1).

`[warn]`
: a non-blocking check failed: the gate still passes, but the skill must fix
  it or explain it to you.

The indented **details** are the to-do list: the exact IDs that miss a test,
the `file:line` of a bad tag, the pending tasks, the tail of a failing test
run. The skill fixes exactly those and runs the gate again. See
{doc}`../tutorial/test` for a full round.

## 3. JSON

Every command has a `--json` form. The skills read specific fields from it
instead of guessing:

| Field | Command | Read by | What it decides |
|---|---|---|---|
| `root`, `context`, `capabilities[].docsPath`, `changes` | {ref}`context <cmd-context>` | every skill, first step | is the project set up; which constraints apply; which docs to read; which change to use |
| `ref` | {ref}`new <cmd-new>` | refine, specify | the name used in every later command |
| `outputPath`, `template`, `instruction`, `exists` | {ref}`instructions <cmd-instructions>` | refine, specify, design, review | where to write the artifact, its structure and rules; update instead of overwrite when `exists` |
| `prefix`, `nextId`, `deltaPath`, `codePath`, `requirements` | {ref}`spec show <cmd-spec>` | specify, design, test, review, close | delta spec path and next free ID; the code folder to read; the whole block to copy for a MODIFIED requirement |
| `rows[].tests`, `rows[].code` | {ref}`trace <cmd-trace>` | test, code, validate | which tests cover a criterion, where a requirement is implemented |
| `findings.*`, `changedFiles` | {ref}`review <cmd-review>` | review | drift candidates in both directions |
| `open[].phase`, `startAt`, `phases`, `handOver` | {ref}`cycle <cmd-cycle>` | build, specify | where the next build cycle starts, or whether to hand over to specify |
| `verdict`, `goBackTo`, `checks[].fix` | {ref}`validate <cmd-validate>` | validate, close | PASS/FAIL, and the phase skill that fixes each failure |
| `artifacts[].status` | {ref}`status <cmd-status>` | specify, build | which artifacts are `done` (re-read them), `ready`, `blocked` or `skipped` |
| `passed`, `checks[]` | {ref}`gate <cmd-gate>` | every phase skill | whether the phase is finished and what is missing |
| `started`, `gates[]` | {ref}`start <cmd-start>` | every phase skill from design on | whether the change moved, and which gate stopped it |

```{admonition} Example: from output to decision
:class: tip feeds

`specworks spec show links --json` returns `"nextId": "REQ-LINK-001"` and
`"deltaPath": "specs/links/spec.md"`. `/specworks-specify` writes the delta spec
to `spec/changes/<change>/specs/links/spec.md` and numbers the first
requirement `REQ-LINK-001`. It never makes up either value.
```
