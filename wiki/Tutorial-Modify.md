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

[`proposal.md`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/proposal.md):

<!-- include: examples/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/proposal.md -->
```markdown
# Proposal: add-link-expiry

## Why

Campaign links must stop working when the campaign ends (open question of add-short-links).

## What Changes

- `shorten(url, ttl=None)` accepts a lifetime in seconds.
- `resolve(code)` rejects an expired code with the new `ExpiredCode`.
- `LinkStore(clock=time.time)` takes a clock, so expiry can be tested.

## Capabilities

### Modified Capabilities

- `links`: REQ-LINK-002 (resolve rejects expired codes) is MODIFIED; REQ-LINK-003 (lifetime) is ADDED.

## Impact

`src/shortlink/store.py`, `src/shortlink/errors.py`. Existing callers are unaffected (defaults).

## Out of Scope

- Changing the lifetime of a URL that already has a code: it keeps its first code and lifetime.
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

> [!NOTE]
> **Why it matters**
>
> `close` replaces the whole REQ-LINK-002 block by ID. A block that leaves out
> `AC-LINK-002.2` would delete that criterion from the living spec.

After copying it back, the final delta:

[`specs/links/spec.md`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/specs/links/spec.md):

<!-- include: examples/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/specs/links/spec.md -->
```markdown
# Spec Delta: links

## ADDED Requirements

### Requirement: REQ-LINK-003 Shorten with a lifetime

The system SHALL accept an optional lifetime in seconds when shortening a URL; the code expires that many seconds after it is issued.

#### Scenario: AC-LINK-003.1 A code resolves before its lifetime ends

- **GIVEN** `shorten(url, ttl=60)` returned code `c` at time 0
- **WHEN** `resolve(c)` is called at time 59
- **THEN** it returns `url`

#### Scenario: AC-LINK-003.2 A lifetime that is not positive is rejected

- **WHEN** `shorten(url, ttl=0)` is called
- **THEN** it raises `ValueError`

## MODIFIED Requirements

### Requirement: REQ-LINK-002 Resolve a code

The system SHALL return the original URL for a code it issued that has not expired, reject a code it did not issue, and reject an expired code with `ExpiredCode`.

#### Scenario: AC-LINK-002.1 A known code resolves

- **GIVEN** `shorten(url)` returned code `c`
- **WHEN** `resolve(c)` is called
- **THEN** it returns `url`

#### Scenario: AC-LINK-002.2 An unknown code is rejected

- **WHEN** `resolve("zzzzzz")` is called on an empty store
- **THEN** it raises `UnknownCode`

#### Scenario: AC-LINK-002.3 An expired code is rejected

- **GIVEN** `shorten(url, ttl=60)` returned code `c` at time 0
- **WHEN** `resolve(c)` is called at time 60
- **THEN** it raises `ExpiredCode`
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

> [!TIP]
> **How the output feeds the skill**
>
> The warning names the requirement that changed and the command that accepts
> it. Re-entering design runs `gate specify` again and records the new
> fingerprints; the tests and code then follow the new specs.

## Extended interfaces

This time the API is *extended*, with defaults so existing callers do not
break:

[`design.md`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/design.md):

<!-- include: examples/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/design.md -->
```markdown
# Design: add-link-expiry

## Decisions

### Injected clock

`LinkStore(clock=time.time)`: tests pass a fake clock instead of sleeping. Serves: REQ-LINK-003, REQ-LINK-002.

## Interfaces

- `src/shortlink/store.py`: `LinkStore(clock: Callable[[], float] = time.time)` (extended, REQ-LINK-003)
- `src/shortlink/store.py`: `LinkStore.shorten(url: str, ttl: float | None = None) -> str`, raises `ValueError` when `ttl <= 0` (extended, REQ-LINK-003)
- `src/shortlink/store.py`: `LinkStore.resolve(code: str) -> str`, also raises `ExpiredCode` (extended, REQ-LINK-002)
- `src/shortlink/errors.py`: `ExpiredCode(ShortlinkError)` (new)
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

[`tests/test_store.py (the tests added by this change)`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/tests/test_store.py):

<!-- include: examples/shortlink/tests/test_store.py start-at="class FakeClock" -->
```python
class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


# @ac AC-LINK-003.1
def test_ac_link_003_1_code_resolves_before_its_lifetime_ends():
    clock = FakeClock()
    store = LinkStore(clock=clock)
    code = store.shorten("https://example.com/a", ttl=60)
    clock.now = 59
    assert store.resolve(code) == "https://example.com/a"


# @ac AC-LINK-003.2
def test_ac_link_003_2_non_positive_lifetime_is_rejected():
    with pytest.raises(ValueError):
        LinkStore().shorten("https://example.com/a", ttl=0)


# @ac AC-LINK-002.3
def test_ac_link_002_3_expired_code_is_rejected():
    clock = FakeClock()
    store = LinkStore(clock=clock)
    code = store.shorten("https://example.com/a", ttl=60)
    clock.now = 60
    with pytest.raises(ExpiredCode):
        store.resolve(code)
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

[`src/shortlink/store.py (final)`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/src/shortlink/store.py):

<!-- include: examples/shortlink/src/shortlink/store.py -->
```python
import secrets
import string
import time
from collections.abc import Callable
from urllib.parse import urlparse

from .errors import ExpiredCode, InvalidUrl, UnknownCode

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6


class LinkStore:
    """An in-memory store of short codes for URLs."""

    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._by_url: dict[str, str] = {}
        self._by_code: dict[str, str] = {}
        self._expires: dict[str, float] = {}

    # @req REQ-LINK-001, REQ-LINK-003
    def shorten(self, url: str, ttl: float | None = None) -> str:
        """Return the 6-character code of ``url``. Implements REQ-LINK-001.

        Raises InvalidUrl when ``url`` is not an http(s) URL with a host.
        """
        if ttl is not None and ttl <= 0:
            raise ValueError(f"ttl must be positive, got {ttl}")
        parts = urlparse(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise InvalidUrl(url)
        if url in self._by_url:
            return self._by_url[url]
        code = self._new_code()
        self._by_url[url] = code
        self._by_code[code] = url
        if ttl is not None:
            self._expires[code] = self._clock() + ttl
        return code

    # @req REQ-LINK-002
    def resolve(self, code: str) -> str:
        """Return the URL a code was issued for. Implements REQ-LINK-002.

        Raises UnknownCode when this store did not issue ``code``.
        """
        if code not in self._by_code:
            raise UnknownCode(code)
        if code in self._expires and self._clock() >= self._expires[code]:
            raise ExpiredCode(code)
        return self._by_code[code]

    def _new_code(self) -> str:
        while True:
            code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
            if code not in self._by_code:
                return code
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

[`review.md`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/review.md):

<!-- include: examples/shortlink/spec/changes/archive/2026-10-17-add-link-expiry/review.md -->
```markdown
# Review: add-link-expiry

Base: `main`

## Findings

None.

## Changed files without tags

- `src/shortlink/errors.py`: adds the `ExpiredCode` type raised by the tagged `resolve` (REQ-LINK-002).

## Summary

No drift: the code, the delta spec and design.md's Interfaces agree.
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

[`src/shortlink/docs/spec.md`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/src/shortlink/docs/spec.md):

<!-- include: examples/shortlink/src/shortlink/docs/spec.md -->
```markdown
# links

## Purpose

Turn long URLs into short codes and resolve the codes back.

## Requirements

### Requirement: REQ-LINK-001 Shorten a URL

The system SHALL return a 6-character code of letters and digits for an http or https URL, and the same code every time the same URL is shortened.

#### Scenario: AC-LINK-001.1 A valid URL gets a code

- **WHEN** `shorten("https://example.com/a")` is called
- **THEN** it returns a 6-character code of letters and digits

#### Scenario: AC-LINK-001.2 The same URL keeps its code

- **GIVEN** `shorten("https://example.com/a")` returned code `c`
- **WHEN** `shorten("https://example.com/a")` is called again
- **THEN** it returns `c`

#### Scenario: AC-LINK-001.3 A URL that is not http(s) is rejected

- **WHEN** `shorten("ftp://example.com")` or `shorten("not a url")` is called
- **THEN** it raises `InvalidUrl`

### Requirement: REQ-LINK-002 Resolve a code

The system SHALL return the original URL for a code it issued that has not expired, reject a code it did not issue, and reject an expired code with `ExpiredCode`.

#### Scenario: AC-LINK-002.1 A known code resolves

- **GIVEN** `shorten(url)` returned code `c`
- **WHEN** `resolve(c)` is called
- **THEN** it returns `url`

#### Scenario: AC-LINK-002.2 An unknown code is rejected

- **WHEN** `resolve("zzzzzz")` is called on an empty store
- **THEN** it raises `UnknownCode`

#### Scenario: AC-LINK-002.3 An expired code is rejected

- **GIVEN** `shorten(url, ttl=60)` returned code `c` at time 0
- **WHEN** `resolve(c)` is called at time 60
- **THEN** it raises `ExpiredCode`

### Requirement: REQ-LINK-003 Shorten with a lifetime

The system SHALL accept an optional lifetime in seconds when shortening a URL; the code expires that many seconds after it is issued.

#### Scenario: AC-LINK-003.1 A code resolves before its lifetime ends

- **GIVEN** `shorten(url, ttl=60)` returned code `c` at time 0
- **WHEN** `resolve(c)` is called at time 59
- **THEN** it returns `url`

#### Scenario: AC-LINK-003.2 A lifetime that is not positive is rejected

- **WHEN** `shorten(url, ttl=0)` is called
- **THEN** it raises `ValueError`
```

[`src/shortlink/docs/requirements.md`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/src/shortlink/docs/requirements.md):

<!-- include: examples/shortlink/src/shortlink/docs/requirements.md -->
```markdown
# Requirements: links

Generated by `specworks close` from spec.md; do not edit by hand.

| Requirement | Title | Acceptance criteria |
|---|---|---|
| REQ-LINK-001 | Shorten a URL | AC-LINK-001.1, AC-LINK-001.2, AC-LINK-001.3 |
| REQ-LINK-002 | Resolve a code | AC-LINK-002.1, AC-LINK-002.2, AC-LINK-002.3 |
| REQ-LINK-003 | Shorten with a lifetime | AC-LINK-003.1, AC-LINK-003.2 |

## History

- 2026-10-17 `add-short-links`: ADDED REQ-LINK-001, REQ-LINK-002
- 2026-10-17 `add-link-expiry`: ADDED REQ-LINK-003; MODIFIED REQ-LINK-002
```
