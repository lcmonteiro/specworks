# Troubleshooting

Messages you will meet in `check`, gates and validate, what they mean, and what
to do.

## Specs and tasks

| Message | Meaning | What to do |
|---|---|---|
| `REQ-...: state the requirement with SHALL or MUST` | a requirement without a normative verb | rewrite it with SHALL/MUST (specify) |
| `AC-X-001.2 is under REQ-X-002; number it AC-X-002.<n>` | criterion numbered under the wrong requirement | renumber it (specify) |
| `AC-... is not covered by any task; mention AC-... or REQ-... in a task` | no task names the criterion or its requirement | add or edit a task (specify) |
| `this MODIFIED block drops AC-...` | MODIFIED is a partial copy | copy the whole block from `spec show --json`, or drop the criterion on purpose with its tests |
| `tasks.md is not written yet` (warning) | expected while writing specs | write `tasks.md` (specify, step 7) |
| `the specs are the ones agreed when specify passed` [warn] | specs edited after specify passed | if intended, `specworks start design` accepts them; tests and code follow |

## Design and test

| Message | Meaning | What to do |
|---|---|---|
| `design.md has an Interfaces section` [FAIL] | the API is not recorded | write `## Interfaces`, or "None" (design) |
| `every file named under Interfaces exists` [FAIL] | a stub file is missing or misspelled | create the stub or fix the path (design) |
| `the existing tests still pass with the stubs` [FAIL] | a stub broke an import or behaviour | fix the stub (design) |
| `every acceptance criterion has a test` [FAIL] + IDs | criteria without an `@ac` tag | write the tests; check tag spelling (test) |
| `AC-LNK-... (no capability uses the prefix LNK; did you mean LINK?)` | a tag with a typo | fix the tag |
| `@ac tags are in test files` [warn] | an `@ac` tag in a file not seen as a test | move it, or set `test_globs` |

## Code and review

| Message | Meaning | What to do |
|---|---|---|
| `every task is done` [FAIL] + tasks | unticked tasks | verify, then `specworks task done N.M` (code) |
| `every requirement has code (@req tag)` [FAIL] | a requirement without a tag | implement and tag it (code) |
| `the test suite passes` [FAIL] + output tail | red suite | fix the code (code) |
| `removed requirements and criteria are gone` [FAIL] | a removed ID is still tagged | delete its code, tests and tags (code) |
| `review.md is written` [FAIL] | no review yet | `specworks instructions review` (review) |
| `changed files without tags are accounted for` [FAIL] + paths | an untagged changed file is not explained | list it under "Changed files without tags" (review) |
| `no open finding in review.md` [FAIL] | findings still open | resolve them, or in a build run the next cycle (`specworks cycle`) |
| `type 'x' is not one of spec-gap, ...` | a finding with an unknown type | use a known type, or add `back to <phase>:` |
| `the change's commits are compared with its base` [warn] | working on the base branch with no start commit | work on a branch, or pass `--base` |

## Commands, diagrams, names

| Message | Meaning | What to do |
|---|---|---|
| `not run (--no-run); run specworks run <key>` [warn] | commands skipped | run without `--no-run` before relying on the result |
| `no 'typecheck' command configured; add it under commands: ...` | `run` with an unknown key | add it to `commands:` |
| a stale pass after changing `.env` or dependencies | ignored files are not in the fingerprint | `specworks run test`, or `--fresh` |
| `diagram SVGs are up to date` [FAIL] / `stale` / `missing` | a `.d2` or the theme changed | `specworks diagrams --change <ref>` |
| `d2 failed on <file>: ... maps must be terminated with }` | D2 syntax error | fix the `.d2` (often an unquoted label with `{` or `:`) |
| `change '<name>' was archived at ...` | the name is taken | pick another name |
| `the ID prefix X is already used by Y` | two capabilities share a prefix | `--prefix` with another one |
| `a change becomes done only through specworks close` | `phase done` refused | run `/specworks-close` |
| `no specworks config (<dir>.yml, e.g. specworks.yml) found` | not in a specworks project | `cd` into it, or `specworks init` |
