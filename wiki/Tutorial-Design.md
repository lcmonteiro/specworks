# 3. design

**Skill**: [/specworks-design](Skills-Design). **Writes**: `## Interfaces` in
`design.md`, and stubs in the code. **Boundary**: a stub has the real
signature, types, errors and doc comment, and a body that only says "not
implemented". No tests, no behaviour.

| Step | Command | Output used for |
|---|---|---|
| 1. Start the phase | `specworks start design --change <ref>` | gate specify must pass; otherwise back to `/specworks-specify` |
| 2. Load the plan | `specworks task list --pending`; `specworks spec show <cap> --json` (`codePath`) | the interface tasks; the code conventions to follow |
| 3. Propose the API | (a table shown to you; agree before writing code) | the agreed API |
| 4. Record it | `## Interfaces` in `design.md` | what the gate and the tests check |
| 5. Create the stubs | (code) | — |
| 6. Check and gate | `specworks run build/typecheck/test`; `specworks task done`; `specworks gate design` | must pass |

## What happens if you skip a phase

`start` refuses to move forward over a phase whose gate does not pass. Trying
`start test` from specify runs both gates, and the design gate fails:

```console
$ specworks start test --change add-short-links
gate specify:
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] tasks.md is written
gate design:
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[FAIL] design.md has an Interfaces section (write "None" when the API does not change)
         write the agreed API under ## Interfaces in design.md (specworks instructions design)
[ok  ] every file named under Interfaces exists
[ok  ] the existing tests still pass with the stubs (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0)
add-short-links: stays in specify; gate design NOT passed
```

The right move:

```console
$ specworks start design --change add-short-links
gate specify:
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] tasks.md is written
add-short-links: phase specify → design
```

Passing `gate specify` through `start` also records a fingerprint of every
requirement in `.change.yaml`; later gates warn when the specs change (see
[Change 2: modifying a capability with a living spec](Tutorial-Modify)):

```yaml
name: add-short-links
created: '2026-10-17T19:55:11'
phase: design
specified:
  REQ-LINK-001: 0f0b38da1971
  REQ-LINK-002: 04c19f6ab6af
```

## Load the plan

```console
$ specworks task list --change add-short-links --pending
[ ] 1.1 Add `LinkStore.shorten` and `InvalidUrl` as stubs (REQ-LINK-001); verify the existing tests pass
[ ] 1.2 Write failing tests for AC-LINK-001.1, AC-LINK-001.2 tagged `@ac`; verify they fail on the stub
[ ] 1.3 Implement `shorten` (REQ-LINK-001) tagged `@req`; verify the 1.2 tests pass
[ ] 2.1 Add `LinkStore.resolve` and `UnknownCode` as stubs (REQ-LINK-002); verify the existing tests pass
[ ] 2.2 Write failing tests for AC-LINK-002.1, AC-LINK-002.2 tagged `@ac`; verify they fail on the stub
[ ] 2.3 Implement `resolve` (REQ-LINK-002) tagged `@req`; verify the 2.2 tests pass
0/6 done
```

## Record the agreed API

The skill proposes the API to you (names, parameters, return and error types,
the requirements each serves, new or extended) and agrees it before writing
code. It is recorded under `## Interfaces`, one entry per interface, each
naming its file in a code span, which is how the gate finds the files to check:

[`design.md (final)`](https://github.com/lcmonteiro/specworks/blob/main/examples/shortlink/spec/changes/archive/2026-10-17-add-short-links/design.md):

<!-- include: examples/shortlink/spec/changes/archive/2026-10-17-add-short-links/design.md -->
```markdown
# Design: add-short-links

## Context

Empty package today; see proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- One code per URL, codes resolvable in O(1).

**Non-Goals:**
- Persistence and expiry (proposal, Out of Scope).

## Decisions

### Two dicts, random base62 codes

`LinkStore` keeps `url -> code` and `code -> url`. A new URL draws random
6-character codes from `secrets.choice` over `[A-Za-z0-9]` until one is free.
Alternative: hash of the URL (refinement Option B), rejected: collisions still
need handling and the user preferred random codes. Serves: REQ-LINK-001, REQ-LINK-002.

### URL validation with urllib.parse

A URL is valid when `urlparse` gives scheme `http`/`https` and a non-empty
host. Serves: AC-LINK-001.3.

## Interfaces

- `src/shortlink/store.py`: `LinkStore()` - an empty in-memory store (REQ-LINK-001, REQ-LINK-002)
- `src/shortlink/store.py`: `LinkStore.shorten(url: str) -> str`, raises `InvalidUrl` (REQ-LINK-001)
- `src/shortlink/store.py`: `LinkStore.resolve(code: str) -> str`, raises `UnknownCode` (REQ-LINK-002)
- `src/shortlink/errors.py`: `ShortlinkError`, `InvalidUrl(ShortlinkError)`, `UnknownCode(ShortlinkError)` (new)

## Diagrams

![Shorten and resolve (REQ-LINK-001, REQ-LINK-002)](diagrams/shorten-flow.svg)

## Risks / Trade-offs

- [the store is lost on restart] -> documented; persistence is a later change.
```

> [!NOTE]
> The gate treats a code span as a file when it has a folder and a dot
> (`src/shortlink/store.py`), or no folder but a code extension (`main.py`).
> `LinkStore.shorten` is not a file. If no span is a file and the section is not
> "None", the gate warns that it cannot check the stubs exist.

## Create the stubs

Error types are complete (they have no behaviour to defer); functions only
raise:

```python
# src/shortlink/errors.py
class ShortlinkError(Exception):
    """Base of every error shortlink raises."""


class InvalidUrl(ShortlinkError):
    """The URL is not an http(s) URL with a host. Implements REQ-LINK-001."""


class UnknownCode(ShortlinkError):
    """The code was not issued by this store. Implements REQ-LINK-002."""
```

```python
# src/shortlink/store.py
class LinkStore:
    """An in-memory store of short codes for URLs."""

    def shorten(self, url: str) -> str:
        """Return the 6-character code of ``url``. Implements REQ-LINK-001.

        Raises InvalidUrl when ``url`` is not an http(s) URL with a host.
        """
        raise NotImplementedError

    def resolve(self, code: str) -> str:
        """Return the URL a code was issued for. Implements REQ-LINK-002.

        Raises UnknownCode when this store did not issue ``code``.
        """
        raise NotImplementedError
```

No `@req` tag yet: `@req` marks *implemented* code, added in the code phase.

## Check and gate

```console
$ specworks run test --change add-short-links
.                                                                        [100%]
1 passed in 0.01s
$ specworks task done 1.1 2.1 --change add-short-links
[x] 1.1 Add `LinkStore.shorten` and `InvalidUrl` as stubs (REQ-LINK-001); verify the existing tests pass
[ ] 1.2 Write failing tests for AC-LINK-001.1, AC-LINK-001.2 tagged `@ac`; verify they fail on the stub
[ ] 1.3 Implement `shorten` (REQ-LINK-001) tagged `@req`; verify the 1.2 tests pass
[x] 2.1 Add `LinkStore.resolve` and `UnknownCode` as stubs (REQ-LINK-002); verify the existing tests pass
[ ] 2.2 Write failing tests for AC-LINK-002.1, AC-LINK-002.2 tagged `@ac`; verify they fail on the stub
[ ] 2.3 Implement `resolve` (REQ-LINK-002) tagged `@req`; verify the 2.2 tests pass
2/6 done
$ specworks gate design --change add-short-links
[ok  ] specs and tasks are valid (specworks check)
[ok  ] specworks check has no warnings
[ok  ] the specs are the ones agreed when specify passed
[ok  ] design.md has an Interfaces section (write "None" when the API does not change)
[ok  ] every file named under Interfaces exists
[ok  ] the existing tests still pass with the stubs (commands.test)
         $ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:56:14)
gate design: passed
```

> [!TIP]
> **How the output feeds the skill**
>
> "The existing tests still pass" proves the stubs broke no import or existing
> behaviour. `same code as the run at ...` means the gate reused the result of
> `specworks run test`, because no code changed since ([The run cache](Reference-Run-Cache)).
> `task done` only flips checkboxes; it never rewrites the rest of `tasks.md`.
> The skill reports a table of interfaces (file, new or extended, requirement)
> and stops: "run `/specworks-test add-short-links`".
