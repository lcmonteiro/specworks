# 6. review

**Skill**: {doc}`../skills/review`. **Writes**: `review.md`; small, local
fixes to code, tests, delta specs or design.md, each agreed with you.
**Boundary**: it removes drift; it does not add features. Inside
{doc}`../skills/build` it fixes nothing: it records open findings for the next
cycle.

| Step | Command | Output used for |
|---|---|---|
| 1. Start | `specworks start review --change <ref>` | gate code must pass |
| 2. Candidates | `specworks review --change <ref> --json` | drift the CLI can see |
| 3. Read the diff | `git diff <base>...HEAD`; re-read specs and design.md | drift only reading can see |
| 4. Decide each finding | (with you) | fix here, or send back |
| 5. Write `review.md` | `specworks instructions review --json` | template and rules |
| 6. Gate and trace | `specworks gate review [--allow-open]`; `specworks trace --write` | must pass |

## Collect the drift candidates

```console
$ specworks start review --change add-short-links
gate code:
...
[ok  ] the test suite passes (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0)
add-short-links: phase code → review
```

::::{tab-set}

:::{tab-item} Text

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

:::

:::{tab-item} JSON (what the skill reads)

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

:::

::::

```{admonition} How the output feeds the skill
:class: tip feeds

- `reqWithoutCode`, `acWithoutTests`, `removedStillTagged`, `unknownTags`
  (spec → code): all empty, the tags are complete.
- `untracedSource` (code → spec): `errors.py` changed but carries no `@req`.
  It is either plumbing for a tagged requirement, a pure refactor, or
  behaviour no requirement describes. Here it is plumbing, and `review.md`
  must say so under "Changed files without tags", or the gate fails.
- The files compared are those changed since `main` (committed, uncommitted
  and untracked), without the workflow folder.
```

## Read the diff

The CLI candidates are only the start. Reading the diff against the specs and
design.md finds what no tag can show: `urlparse("https://")` gives scheme
`https` and an empty `netloc`, so `shorten("https://")` returns a code, while
design.md's decision says "a non-empty host". The test for `AC-LINK-001.3`
asserts too little to notice. That is a finding of type **`test-gap`** (a
test that would not fail if the behaviour broke), plus a code fix.

The skill checks, in both directions:

- each requirement and criterion → code: does the tagged code do exactly what
  it says, errors and edge cases included?
- each change in the code → spec: is every new behaviour covered by a
  requirement?
- each test → its criterion: would it fail if the behaviour broke?
- the tags, the design/API (Interfaces and Decisions), and quality that
  matters (security, data loss, error handling).

## The gate before `review.md` exists

```console
$ specworks gate review --change add-short-links --base main
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[FAIL] review.md is written
         write review.md (specworks instructions review)
[ok  ] every finding in review.md is readable (- [ ] R<n> ...)
[FAIL] no open finding in review.md
[ok  ] every requirement has code (@req tag)
[ok  ] every acceptance criterion has a test (@ac tag)
[ok  ] no tag refers to an unknown requirement or criterion
[ok  ] removed requirements and criteria are gone from tests and code
[FAIL] changed files without tags are accounted for in review.md (base main)
         src/shortlink/errors.py
[ok  ] the test suite passes (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:56:47)
gate review: NOT passed
```

## Decide and record

The skill proposes the fix to you and decides where it is made. Standalone, a
change this small would be fixed right here (test and code, then
`specworks run test`). In `/specworks-build`, shown here, every finding that
needs work is recorded **open**, with the agreed proposal and the phase that
carries it out:

```markdown
# Review: add-short-links

Base: `main`

## Findings

- [ ] R1 **test-gap** AC-LINK-001.3 tests only `ftp://` and `not a url`; `shorten("https://")` (no host) returns a code, although design.md (URL validation) requires a non-empty host (`src/shortlink/store.py:24`)
  - **Decision**: back to test: add `"https://"` and `"http:///path"` to the AC-LINK-001.3 cases; then code: check `netloc` as design.md says. Agreed with the user.

## Changed files without tags

- `src/shortlink/errors.py`: error types only, used by the tagged `shorten` (REQ-LINK-001) and `resolve` (REQ-LINK-002); no behaviour of their own.

## Summary

One test gap: hostless URLs are accepted. Sent back to test, then code.
```

An open finding fails the plain gate; `--allow-open` (used inside a build)
turns it into a warning, while every other check must still pass:

```console
$ specworks gate review --change add-short-links --base main
...
[FAIL] no open finding in review.md
         R1 **test-gap** AC-LINK-001.3 tests only `ftp://` and `not a url`; ...
...
[ok  ] changed files without tags are accounted for in review.md (base main)
...
gate review: NOT passed
$ specworks gate review --change add-short-links --base main --allow-open
...
[warn] no open finding in review.md
         R1 **test-gap** AC-LINK-001.3 tests only `ftp://` and `not a url`; ...
...
gate review: passed
```

## Where the next cycle starts

::::{tab-set}

:::{tab-item} Text

```console
$ specworks cycle --change add-short-links
R1 test-gap -> test
next cycle: test -> code -> review
```

:::

:::{tab-item} JSON

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
    {
      "id": "R1",
      "type": "test-gap",
      "text": "**test-gap** AC-LINK-001.3 tests only `ftp://` and `not a url`; ...",
      "phase": "test"
    }
  ],
  "startAt": "test",
  "phases": ["test", "code", "review"],
  "handOver": null
}
```

:::

::::

```{admonition} How the output feeds the skill
:class: tip feeds

`/specworks-build` shows the open findings and asks "Start cycle 2 from test:
test → code → review?". On yes, it runs the `startAt` phase's skill, which
moves the change back with `specworks start test`. `handOver` would be
`/specworks-specify` for a spec finding: the build stops there.
```

## How `cycle` routes other findings

The same command on a different `review.md` (temporarily, to show the rules):

```markdown
- [ ] R1 **code-gap** resolve is case-sensitive but codes are read aloud
- [ ] R2 **design-gap** `shorten` should return a `ShortLink` object, not a str
- [ ] R3 **spec-gap** nothing says what happens with a URL longer than 2048 chars
  - **Decision**: back to specify: add REQ-LINK-003 (reject URLs over 2048 chars)
```

```console
$ specworks cycle --change add-short-links
R1 code-gap -> code
R2 design-gap -> design
R3 spec-gap -> specify
a spec finding: stop the build and run /specworks-specify add-short-links
```

After `/specworks-specify` carries out R3, it adds
`  - done in specify: ADDED REQ-LINK-003 with AC-LINK-003.1` under it (and
leaves the box open). The finding then needs the phases after specify:

```console
$ specworks cycle --change add-short-links
R1 code-gap -> code
R2 design-gap -> design
R3 spec-gap -> design
next cycle: design -> test -> code -> review
```

A finding type the parser does not know cannot be routed, so the gate refuses
it:

```markdown
- [ ] R1 **style** naming of `_new_code`
```

```console
$ specworks gate review --change add-short-links --base main --allow-open --no-run
[FAIL] every finding in review.md is readable (- [ ] R<n> ...)
         R1: type 'style' is not one of spec-gap, design-gap, test-gap, code-gap, tag, quality; name one, or add a Decision 'back to <specify|design|test|code>: ...'
```

All routing rules: {doc}`../reference/findings`.
