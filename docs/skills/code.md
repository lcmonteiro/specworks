# /specworks-code

:Phase: code
:Writes: code tagged `@req <REQ-ID>`; ticks tasks
:Next: `/specworks-review <ref>`
:Example: {doc}`../tutorial/code`

Make the failing tests pass by writing the code the tasks describe, and
nothing more. Use it when a change has its failing tests, or when you say
"implement the change", "make the acceptance tests pass" or "specworks code".

## Steps

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 1 | Start the phase | `specworks start code --change <ref>` | `gate test`; criteria without tests → `/specworks-test` (only with your explicit agreement does it skip tests, via `specworks phase code`) |
| 2 | Load the plan | `specworks task list --pending`; `specworks trace --json` | the tasks in order; which tests cover each criterion; where stubs live |
| 3 | Each task, in order | code → `specworks run test` → `specworks task done <N.M>` | the task's verification; tick only when it passed |
| 4 | Project checks | `specworks run test`, `run lint`, `run typecheck` | what fails, to fix |
| 5 | Gate and trace | `specworks gate code`; `specworks trace --write` | pending tasks, untagged requirements, unknown tags, removed IDs still tagged, a red suite |
| 6 | Report and stop | — | tasks done, files changed, where each requirement is implemented, test results, any deviation recorded in design.md; "run `/specworks-review <ref>`" |

Each task: announce it (`Task 2.1: ...`), read its requirements, criteria and
tests, write the smallest code that makes them pass the way the requirement
intends, replace the stub, and tag the entry point:

```python
# @req REQ-AUTH-003
def request_password_reset(email: str) -> None: ...
```

For REMOVED requirements: delete their code and `@req` tags.

## When it stops and asks

- a task or requirement is unclear, or two conflict;
- the tests and the spec disagree, or a test looks wrong (a test changes only
  if it contradicts its criterion, with your agreement, and the report says so);
- the design does not work in practice (the change is proposed, and recorded
  under the decision in design.md once you agree);
- work the tasks do not cover (a new task, or a new requirement through
  `/specworks-specify`).

## Guardrails

- The specs and tests are the contract: delta specs are not edited here.
- No scope creep: no features, refactors or clean-ups the tasks do not ask for.
- A task is ticked only after its verification passed.
- `@req` marks real implementations, never stubs or unrelated code.

## Source

````{dropdown} specworks-code/SKILL.md
:icon: code

```{literalinclude} ../../src/specworks/skills/specworks-code/SKILL.md
:language: markdown
```
````
