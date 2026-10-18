# Review findings and build cycles

## A finding

A finding in `review.md` is a checkbox with an ID and a type in bold; the
indented lines under it belong to it:

```markdown
- [ ] R2 **design-gap** `reset()` returns None; callers need the token (REQ-AUTH-003)
  - **Decision**: back to design: return `ResetToken` from `ResetService.request_reset`
```

- `- [ ]` open, `- [x]` resolved. `*`, `+` and `1.` bullets, and a bold
  `**R1**`, are read too.
- Any other checkbox at the top level is reported, never skipped: a finding
  the parser could not see would let the review gate pass with it open.
- HTML comments and code fences are ignored (a finding in a fence is an
  example).

## Types

| Type | Means | Phase that resolves it |
|---|---|---|
| `spec-gap` | behaviour no requirement describes, or a requirement that is wrong | specify (stops a build) |
| `design-gap` | the code differs from Interfaces/Decisions, or implementing proved them wrong | design |
| `test-gap` | a test does not really check its criterion | test |
| `code-gap` | the code misses part of a requirement | code |
| `tag` | a tag missing, misplaced or to a wrong ID | code |
| `quality` | security, data loss, error handling, an obvious bug | code |

An open finding with another type and no `back to` is an error:

```text
R1: type 'style' is not one of spec-gap, design-gap, test-gap, code-gap, tag, quality; name one, or add a Decision 'back to <specify|design|test|code>: ...'
```

## Decisions

`back to <specify|design|test|code>: <proposal>`
: sends the finding to that phase, overriding its type. It stays open.

`done in <specify|design|test|code>: <what changed>`
: that phase carried out its part; the finding now needs the phase **after**
  it (`done in specify` → design). It stays open until review confirms it.

`accepted: <reason>`
: closes the finding without a change; only with your explicit agreement.

code fixed / spec updated / design updated
: the fix was made in review; the box is ticked.

## Where the next cycle starts

`specworks cycle` takes the earliest phase any open finding needs, and runs
every later phase up to review:

| Earliest phase needed | Next cycle |
|---|---|
| code | code → review |
| test | test → code → review |
| design | design → test → code → review |
| specify | none: `handOver: /specworks-specify`; the build stops |

Examples of every case, with real output: [6. review](Tutorial-Review).

## Changed files without tags

Under `## Changed files without tags`, every file `specworks review` lists in
`untracedSource` or `untracedTests` must appear as a whole path, with why it
needs no tag (config, refactor, helper of REQ-...) or the finding that covers
it:

```markdown
## Changed files without tags

- `src/shortlink/errors.py`: error types only, used by the tagged `shorten` (REQ-LINK-001) and `resolve` (REQ-LINK-002); no behaviour of their own.
```
