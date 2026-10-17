# Gate checks

`specworks gate <phase> --change <ref>` runs a list of checks. A gate passes
when none of its **blocking** checks fails; warnings never block. A check that
does not apply is not shown (for example "the specs are the ones agreed..."
before `start` ever passed specify). The checks are defined once, in
`src/specworks/workflow/checks.py` and `gate.py`, and shared by the gates and
validate.

✔ blocking · warn: shown as `[warn]`, never blocks

| Check | specify | design | test | code | review |
|---|:-:|:-:|:-:|:-:|:-:|
| specs and tasks are valid (`specworks check`) | ✔ | ✔ | ✔ | ✔ | ✔ |
| `specworks check` has no warnings | warn | warn | warn | warn | warn |
| `tasks.md` is written | ✔ | | | | |
| the specs are the ones agreed when specify passed | | warn | warn | warn | warn |
| design.md has an Interfaces section | | ✔ | | | |
| every file named under Interfaces exists | | ✔ | | | |
| Interfaces names the file of each interface | | warn | | | |
| the stubs build (`commands.build`, `commands.typecheck`, when configured) | | ✔ | | | |
| the existing tests still pass with the stubs (`commands.test`) | | ✔ ¹ | | | |
| every acceptance criterion has a test (`@ac`) | | | ✔ | ✔ | ✔ |
| no tag refers to an unknown requirement or criterion | | | ✔ | ✔ | ✔ |
| `@ac` tags are in test files | | | warn | | |
| removed requirements and criteria are gone from tests and code | | | warn | ✔ | ✔ |
| every task is done | | | | ✔ | |
| every requirement has code (`@req`) | | | | ✔ | ✔ |
| the test suite passes (`commands.test`) | | | | ✔ | ✔ |
| `review.md` is written | | | | | ✔ |
| every finding in `review.md` is readable | | | | | ✔ |
| no open finding in `review.md` | | | | | ✔ ² |
| changed files without tags are accounted for in `review.md` | | | | | ✔ |
| the change's commits are compared with its base | | | | | warn ³ |
| the tests of each MODIFIED requirement changed with it | | | | | warn |

¹ Only a warning once the change already has `@ac` tests: in a later build
cycle, changing an API turns its tests red on purpose until the code phase.

² A warning with `--allow-open` (inside `/specworks-build`).

³ Only when HEAD is on the base branch and no commit marks where the change
started.

The `validate` gate runs the checks of {doc}`validate`.

## Project commands in gates

`--no-run` turns every project-command check into a warning:

```text
[warn] the existing tests still pass with the stubs (commands.test)
         not run (--no-run); run `specworks run test`
```

A missing `commands.test` is a failure (the gate cannot prove anything
without it). A failing run shows the command, folder, exit code and the tail
of its output. A result reused from the same code says so:

```text
[ok  ] the test suite passes (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:56:40)
```

## Where each check is in the tutorial

| Check failing | Shown in |
|---|---|
| design.md has an Interfaces section | {doc}`../tutorial/design` |
| every acceptance criterion has a test; unknown tag | {doc}`../tutorial/test` |
| every task is done | {doc}`../tutorial/code` |
| review.md is written; files accounted for; open finding | {doc}`../tutorial/review` |
| every finding is readable (unknown type) | {doc}`../tutorial/review` |
| the specs are the ones agreed when specify passed | {doc}`../tutorial/modify` |
