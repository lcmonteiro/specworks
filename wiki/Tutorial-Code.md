# 5. code

**Skill**: [/specworks-code](Skills-Code). **Writes**: the implementation, tagged
`@req`. **Boundary**: the specs and tests are the contract; no scope creep; a
task is ticked only after its verification passed.

| Step | Command | Output used for |
|---|---|---|
| 1. Start | `specworks start code --change <ref>` | gate test must pass |
| 2. Load | `specworks task list --pending`; `specworks trace --json` | tasks in order; which tests cover what |
| 3. Each task | code → `specworks run test` → `specworks task done N.M` | the task's verification |
| 4. Project checks | `specworks run test`, `run lint`, `run typecheck` | fix what fails |
| 5. Gate and trace | `specworks gate code`; `specworks trace --write` | must pass |

```console
$ specworks start code --change add-short-links
gate test:
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[ok  ] every acceptance criterion has a test (@ac tag)
[ok  ] no tag refers to an unknown requirement or criterion
[ok  ] @ac tags are in test files (configure test_globs if your tests live elsewhere)
[ok  ] removed requirements and criteria are gone from tests and code
add-short-links: phase test → code
```

## The implementation

It replaces the stubs. Each requirement is tagged at its entry point:

```python
import secrets
import string
from urllib.parse import urlparse

from .errors import InvalidUrl, UnknownCode

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6


class LinkStore:
    """An in-memory store of short codes for URLs."""

    def __init__(self) -> None:
        self._by_url: dict[str, str] = {}
        self._by_code: dict[str, str] = {}

    # @req REQ-LINK-001
    def shorten(self, url: str) -> str:
        """Return the 6-character code of ``url``. Implements REQ-LINK-001.

        Raises InvalidUrl when ``url`` is not an http(s) URL with a host.
        """
        if urlparse(url).scheme not in ("http", "https"):
            raise InvalidUrl(url)
        if url in self._by_url:
            return self._by_url[url]
        code = self._new_code()
        self._by_url[url] = code
        self._by_code[code] = url
        return code

    # @req REQ-LINK-002
    def resolve(self, code: str) -> str:
        """Return the URL a code was issued for. Implements REQ-LINK-002.

        Raises UnknownCode when this store did not issue ``code``.
        """
        try:
            return self._by_code[code]
        except KeyError:
            raise UnknownCode(code) from None

    def _new_code(self) -> str:
        while True:
            code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
            if code not in self._by_code:
                return code
```

> [!WARNING]
> This code has a gap on purpose: it checks the scheme but not the host, so
> `shorten("https://")` is accepted although design.md says "a non-empty host".
> The tests do not catch it. The review will ([6. review](Tutorial-Review)).

```console
$ specworks run test --change add-short-links
.......                                                                  [100%]
7 passed in 0.02s
```

## Forgetting to tick the tasks

```console
$ specworks gate code --change add-short-links
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[FAIL] every task is done (specworks task list --pending)
         1.3 Implement `shorten` (REQ-LINK-001) tagged `@req`; verify the 1.2 tests pass
         2.3 Implement `resolve` (REQ-LINK-002) tagged `@req`; verify the 2.2 tests pass
[ok  ] every requirement has code (@req tag)
[ok  ] every acceptance criterion has a test (@ac tag)
[ok  ] no tag refers to an unknown requirement or criterion
[ok  ] removed requirements and criteria are gone from tests and code
[ok  ] the test suite passes (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:56:40)
gate code: NOT passed
```

> [!TIP]
> **How the output feeds the skill**
>
> The pending tasks are listed by number. The skill ticks a task only after its
> verification passed (here: the tests named in task 1.2 and 2.2 pass), so it
> runs `task done` for exactly those, never ahead.

```console
$ specworks task done 1.3 2.3 --change add-short-links
...
6/6 done
$ specworks run lint --change add-short-links
All checks passed!
$ specworks gate code --change add-short-links
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[ok  ] every task is done (specworks task list --pending)
[ok  ] every requirement has code (@req tag)
[ok  ] every acceptance criterion has a test (@ac tag)
[ok  ] no tag refers to an unknown requirement or criterion
[ok  ] removed requirements and criteria are gone from tests and code
[ok  ] the test suite passes (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:56:40)
gate code: passed
```

> [!NOTE]
> Ticking tasks did not invalidate the test result: files in the workflow
> folder (`spec/`) are not part of the code fingerprint
> ([The run cache](Reference-Run-Cache)).

The work is committed on the branch before the review, so
`git diff main...HEAD` shows it. The skill reports tasks done, files changed,
where each requirement is implemented (from the trace) and the test results,
then stops: "run `/specworks-review add-short-links`".
