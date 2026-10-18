# 7. The second build cycle

Cycle 2 runs test → code → review, each phase working only on finding R1.
This is what [/specworks-build](Skills-Build) does after you answer "yes" to "Start
cycle 2 from test?".

## test

Going back from review to test needs only the gate of the phase before test
(design):

```console
$ specworks start test --change add-short-links
gate design:
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[ok  ] design.md has an Interfaces section (write "None" when the API does not change)
[ok  ] every file named under Interfaces exists
[ok  ] the existing tests still pass with the stubs (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:56:47)
add-short-links: phase review → test
```

The two hostless URLs join the `AC-LINK-001.3` cases:

```python
@pytest.mark.parametrize("url", ["ftp://example.com", "not a url", "https://", "http:///path"])
```

```console
$ specworks run test --change add-short-links
=========================== short test summary info ============================
FAILED tests/test_store.py::test_ac_link_001_3_non_http_url_is_rejected[https://]
FAILED tests/test_store.py::test_ac_link_001_3_non_http_url_is_rejected[http:///path]
2 failed, 7 passed in 0.02s
```

> [!TIP]
> **How the output feeds the skill**
>
> Red for the right reason: the two new cases fail with `DID NOT RAISE
> InvalidUrl`, which is exactly the gap R1 describes. The other tests still
> pass.

## code

The fix follows the design decision:

```python
        parts = urlparse(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise InvalidUrl(url)
```

```console
$ specworks start code --change add-short-links
...
add-short-links: phase test → code
$ specworks gate code --change add-short-links
...
[ok  ] the test suite passes (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0)
gate code: passed
```

## review

The review checks that the proposal was carried out, ticks R1 and records
what each phase did:

[`review.md (final)`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/spec/changes/archive/2026-10-17-add-short-links/review.md):

<!-- include: examples/shortlink/spec/changes/archive/2026-10-17-add-short-links/review.md -->
```markdown
# Review: add-short-links

Base: `main`

## Findings

- [x] R1 **test-gap** AC-LINK-001.3 tests only `ftp://` and `not a url`; `shorten("https://")` (no host) returns a code, although design.md (URL validation) requires a non-empty host (`src/shortlink/store.py:24`)
  - **Decision**: back to test: add `"https://"` and `"http:///path"` to the AC-LINK-001.3 cases; then code: check `netloc` as design.md says. Agreed with the user.
  - done in test: `https://` and `http:///path` added to the AC-LINK-001.3 cases (failed: DID NOT RAISE).
  - done in code: `shorten` checks `netloc`; all tests pass.

## Changed files without tags

- `src/shortlink/errors.py`: error types only, used by the tagged `shorten` (REQ-LINK-001) and `resolve` (REQ-LINK-002); no behaviour of their own.

## Summary

One test gap (hostless URLs accepted), fixed in cycle 2 (test, code). No spec or API change.
```

```console
$ specworks start review --change add-short-links
add-short-links: phase code → review
$ specworks cycle --change add-short-links
no open findings: the build is done; next is /specworks-validate
$ specworks gate review --change add-short-links --base main
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[ok  ] review.md is written
[ok  ] every finding in review.md is readable (- [ ] R<n> ...)
[ok  ] no open finding in review.md
[ok  ] every requirement has code (@req tag)
[ok  ] every acceptance criterion has a test (@ac tag)
[ok  ] no tag refers to an unknown requirement or criterion
[ok  ] removed requirements and criteria are gone from tests and code
[ok  ] changed files without tags are accounted for in review.md (base main)
[ok  ] the test suite passes (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:57:19)
gate review: passed
```

> [!TIP]
> **How the output feeds the skill**
>
> `no open findings: the build is done` ends the build: it writes the trace,
> summarises each cycle (API, tests, code, findings found, resolved and
> accepted) and suggests `/specworks-validate add-short-links`.
