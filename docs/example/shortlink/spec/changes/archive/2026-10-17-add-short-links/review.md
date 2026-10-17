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
