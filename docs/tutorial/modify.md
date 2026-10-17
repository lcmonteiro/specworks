# Change 2: modifying a capability with a living spec

`add-link-expiry` answers the open question from the first refinement ("Should
codes expire?"). It is small, so it skips refine:

```console
$ specworks new add-link-expiry
$ specworks phase specify --change add-link-expiry
```

Only what differs from change 1 is shown.

## The living spec is the starting point

`spec show --json` now returns the existing requirements with every
scenario's text: exactly what a MODIFIED block must copy.

```console
$ specworks spec show links --json
{
  "ref": "links",
  "module": "(top)",
  "name": "links",
  "new": false,
  "prefix": "LINK",
  "nextId": "REQ-LINK-003",
  "deltaPath": "specs/links/spec.md",
  "codePath": "src/shortlink",
  "livingSpec": "src/shortlink/docs/spec.md",
  "hasSpec": true,
  "purpose": "Turn long URLs into short codes and resolve the codes back.",
  "requirements": [
    {
      "id": "REQ-LINK-001",
      "title": "Shorten a URL",
      "scenarios": [
        {
          "id": "AC-LINK-001.1",
          "title": "A valid URL gets a code",
          "text": "- **WHEN** `shorten(\"https://example.com/a\")` is called\n- **THEN** it returns a 6-character code of letters and digits"
        },
        ...
```

```{literalinclude} ../example/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/proposal.md
:language: markdown
:caption: proposal.md
```

## A partial MODIFIED block is caught

The first delta spec adds `AC-LINK-002.3` but forgets to copy
`AC-LINK-002.2`:

```markdown
## MODIFIED Requirements

### Requirement: REQ-LINK-002 Resolve a code

The system SHALL return the original URL for a code it issued that has not expired, reject a code it did not issue, and reject an expired code.

#### Scenario: AC-LINK-002.1 A known code resolves
...
#### Scenario: AC-LINK-002.3 An expired code is rejected
...
```

```console
$ specworks check --change add-link-expiry
warning spec/changes/add-link-expiry/specs/links/spec.md:22: REQ-LINK-002: this MODIFIED block drops AC-LINK-002.2; copy the whole block from the living spec, or drop a criterion only on purpose (with its tests)
add-link-expiry: valid (0 errors, 1 warnings)
```

```{admonition} Why it matters
:class: important

`close` replaces the whole REQ-LINK-002 block by ID. A block that leaves out
`AC-LINK-002.2` would delete that criterion from the living spec.
```

After copying it back, the final delta:

```{literalinclude} ../example/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/specs/links/spec.md
:language: markdown
:caption: specs/links/spec.md
```

```console
$ specworks check --change add-link-expiry
add-link-expiry: valid (0 errors, 0 warnings)
$ specworks start design --change add-link-expiry
add-link-expiry: phase specify → design
```

```yaml
specified:
  REQ-LINK-003: f9d27063c4e9
  REQ-LINK-002: 0da9b328e3a8
```

## Specs edited after specify passed

Changing REQ-LINK-002's text during design (adding "with `ExpiredCode`") is
noticed by every later gate:

```console
$ specworks gate design --change add-link-expiry --no-run
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[warn] the specs are the ones agreed when specify passed
         REQ-LINK-002 changed
         if that is intended, `specworks start design --change add-link-expiry` re-checks specify and accepts them; the tests and code then follow the new specs
[FAIL] design.md has an Interfaces section (write "None" when the API does not change)
         write the agreed API under ## Interfaces in design.md (specworks instructions design)
[ok  ] every file named under Interfaces exists
[warn] the existing tests still pass with the stubs (commands.test)
         not run (--no-run); run `specworks run test`
gate design: NOT passed
$ specworks start design --change add-link-expiry   # accept the new specs
add-link-expiry: phase design → design
```

```{admonition} How the output feeds the skill
:class: tip feeds

The warning names the requirement that changed and the command that accepts
it. Re-entering design runs `gate specify` again and records the new
fingerprints; the tests and code then follow the new specs.
```

## Extended interfaces

This time the API is *extended*, with defaults so existing callers do not
break:

```{literalinclude} ../example/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/design.md
:language: markdown
:caption: design.md
```

The stub only covers the new path (`if ttl is not None: raise
NotImplementedError`), so the existing behaviour and its tests keep working:

```console
$ specworks gate design --change add-link-expiry
...
[ok  ] every file named under Interfaces exists
[ok  ] the existing tests still pass with the stubs (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0)
gate design: passed
```

## test and code

The new tests use a fake clock through the injected `clock`:

```{literalinclude} ../example/shortlink/tests/test_store.py
:language: python
:caption: tests/test_store.py (the tests added by this change)
:start-at: class FakeClock
```

```console
$ specworks run test --change add-link-expiry
FAILED tests/test_store.py::test_ac_link_003_1_code_resolves_before_its_lifetime_ends
FAILED tests/test_store.py::test_ac_link_003_2_non_positive_lifetime_is_rejected
FAILED tests/test_store.py::test_ac_link_002_3_expired_code_is_rejected - Not...
3 failed, 9 passed in 0.04s
$ specworks gate test --change add-link-expiry
gate test: passed
```

One tag can name several requirements: `shorten` now implements two.

```{literalinclude} ../example/shortlink/src/shortlink/store.py
:language: python
:caption: src/shortlink/store.py (final)
```

```console
$ specworks gate code --change add-link-expiry
...
[ok  ] the test suite passes (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0)
gate code: passed
```

## review: the tests of a MODIFIED requirement must change

A MODIFIED requirement gets one more check: its tests must have changed on the
branch, since old tests only check the old behaviour. The `AC-LINK-002.3` test
was added to `tests/test_store.py`, so it passes:

```console
$ specworks review --change add-link-expiry --base main
...
changed code files without `@req` tags: 1
  src/shortlink/errors.py
changed test files without `@ac` tags: 0
1 drift candidates
$ specworks gate review --change add-link-expiry --base main
...
[ok  ] the tests of each MODIFIED requirement changed with it
[ok  ] the test suite passes (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:58:38)
gate review: passed
```

```{literalinclude} ../example/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/review.md
:language: markdown
:caption: review.md
```

## validate and close: a MODIFIED merge

```console
$ specworks validate --change add-link-expiry --base main
add-link-expiry: PASS (0 critical, 0 warnings)
$ specworks close --change add-link-expiry --base main --dry-run --no-run
would merge links -> src/shortlink/docs/spec.md: ADDED REQ-LINK-003; MODIFIED REQ-LINK-002
$ specworks close --change add-link-expiry --base main
merged links -> src/shortlink/docs/spec.md: ADDED REQ-LINK-003; MODIFIED REQ-LINK-002
archived -> spec/changes/archive/2026-10-17-add-link-expiry
```

REQ-LINK-002 is replaced in place (same position, all three criteria), and
REQ-LINK-003 is appended:

```{literalinclude} ../example/shortlink/src/shortlink/docs/spec.md
:language: markdown
:caption: src/shortlink/docs/spec.md
```

```{literalinclude} ../example/shortlink/src/shortlink/docs/requirements.md
:language: markdown
:caption: src/shortlink/docs/requirements.md
```
