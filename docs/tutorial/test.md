# 4. test

**Skill**: {doc}`../skills/test`. **Writes**: tests tagged `@ac`.
**Boundary**: no behaviour, no new interfaces (a missing one sends you back to
`/specworks-design`); never weaken, skip or mark a test as expected to fail.

| Step | Command | Output used for |
|---|---|---|
| 1. Start | `specworks start test --change <ref>` | gate design must pass |
| 2. Load | `specworks task list --pending`; `specworks trace --json` | the tests that already cover MODIFIED or REMOVED criteria |
| 3. API covers every criterion? | (read design.md Interfaces) | otherwise back to design |
| 4. Write tests | one or more per criterion, tagged `@ac` | — |
| 5. Run them | `specworks run test --change <ref>` | **red for the right reason** |
| 6. Gate and trace | `specworks task done`; `specworks gate test`; `specworks trace --write` | must pass |

```console
$ specworks start test --change add-short-links
gate design:
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[ok  ] design.md has an Interfaces section (write "None" when the API does not change)
[ok  ] every file named under Interfaces exists
[ok  ] the existing tests still pass with the stubs (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:56:14)
add-short-links: phase design → test
```

## A first attempt, and what the gate says

Two mistakes: no test for `AC-LINK-001.3`, and a typo in a tag
(`AC-LNK-002.2`):

```console
$ specworks gate test --change add-short-links
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[FAIL] every acceptance criterion has a test (@ac tag)
         AC-LINK-001.3
         AC-LINK-002.2
[FAIL] no tag refers to an unknown requirement or criterion
         AC-LNK-002.2 at tests/test_store.py:28 (no capability uses the prefix LNK; did you mean LINK?)
[ok  ] @ac tags are in test files (configure test_globs if your tests live elsewhere)
[ok  ] removed requirements and criteria are gone from tests and code
gate test: NOT passed
```

```{admonition} How the output feeds the skill
:class: tip feeds

The details are the exact to-do list. `AC-LINK-001.3` has no test at all.
`AC-LINK-002.2` has one, but its tag is misspelled, so it does not count; the
second check points at the line and suggests the right prefix. The skill
writes the missing test, fixes the tag, and runs the gate again.
```

## The tests

```python
import re

import pytest

from shortlink.errors import InvalidUrl, UnknownCode
from shortlink.store import LinkStore


# @ac AC-LINK-001.1
def test_ac_link_001_1_valid_url_gets_a_code():
    code = LinkStore().shorten("https://example.com/a")
    assert re.fullmatch(r"[A-Za-z0-9]{6}", code)


# @ac AC-LINK-001.2
def test_ac_link_001_2_same_url_keeps_its_code():
    store = LinkStore()
    assert store.shorten("https://example.com/a") == store.shorten("https://example.com/a")


# @ac AC-LINK-001.3
@pytest.mark.parametrize("url", ["ftp://example.com", "not a url"])
def test_ac_link_001_3_non_http_url_is_rejected(url):
    with pytest.raises(InvalidUrl):
        LinkStore().shorten(url)


# @ac AC-LINK-002.1
def test_ac_link_002_1_known_code_resolves():
    store = LinkStore()
    code = store.shorten("https://example.com/a")
    assert store.resolve(code) == "https://example.com/a"


# @ac AC-LINK-002.2
def test_ac_link_002_2_unknown_code_is_rejected():
    with pytest.raises(UnknownCode):
        LinkStore().resolve("zzzzzz")
```

Each test checks exactly its criterion's WHEN/THEN through the public API
(GIVEN → arrange, WHEN → act, THEN → assert), is named after the criterion, and
carries its tag in a comment right above it.

## Red for the right reason

The gate does not run the tests; the skill does, and reads the failures
(output abridged):

```console
$ specworks run test --change add-short-links
.FFFFFF                                                                  [100%]
=================================== FAILURES ===================================
___________________ test_ac_link_001_1_valid_url_gets_a_code ___________________
...
>       raise NotImplementedError
E       NotImplementedError

src/shortlink/store.py:9: NotImplementedError
...
=========================== short test summary info ============================
FAILED tests/test_store.py::test_ac_link_001_1_valid_url_gets_a_code - NotImp...
FAILED tests/test_store.py::test_ac_link_001_2_same_url_keeps_its_code - NotI...
FAILED tests/test_store.py::test_ac_link_001_3_non_http_url_is_rejected[ftp://example.com]
FAILED tests/test_store.py::test_ac_link_001_3_non_http_url_is_rejected[not a url]
FAILED tests/test_store.py::test_ac_link_002_1_known_code_resolves - NotImple...
FAILED tests/test_store.py::test_ac_link_002_2_unknown_code_is_rejected - Not...
6 failed, 1 passed in 0.04s
```

```{admonition} How the output feeds the skill
:class: tip feeds

The skill checks three things in this output:

1. every new test **fails**;
2. each fails on `NotImplementedError` (the stub), not on an `ImportError`,
   a collection error or a syntax error, which would be bugs in the tests or
   stubs to fix now;
3. the existing test (`1 passed`) still passes.

A new test that already *passed* would mean it checks nothing new, or the
behaviour already exists: the skill looks at it and tells you.
```

## Gate and trace

```console
$ specworks task done 1.2 2.2 --change add-short-links
...
4/6 done
$ specworks gate test --change add-short-links
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[ok  ] every acceptance criterion has a test (@ac tag)
[ok  ] no tag refers to an unknown requirement or criterion
[ok  ] @ac tags are in test files (configure test_globs if your tests live elsewhere)
[ok  ] removed requirements and criteria are gone from tests and code
gate test: passed
```

`specworks trace --json` now lists the tests of each criterion (first row):

```json
{
  "capability": "links",
  "req": "REQ-LINK-001",
  "title": "Shorten a URL",
  "section": "ADDED",
  "ac": "AC-LINK-001.1",
  "ac_title": "A valid URL gets a code",
  "tasks": ["1.1", "1.2", "1.3"],
  "tests": ["tests/test_store.py:9"],
  "code": []
}
```

The skill reports one row per criterion (test, and why it fails), says the
suite is red on purpose until the code phase, and stops: "run
`/specworks-code add-short-links`".
