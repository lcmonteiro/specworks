# IDs, tags and traceability

## Capabilities

A **capability** is a durable behaviour of the system owned by a code folder,
registered in the config:

```yaml
capabilities:
  links:
    path: src/shortlink
    description: Create short codes for URLs and resolve them
    prefix: LINK
```

Its living docs go to `<path>/<docs_dir>/` (`src/shortlink/docs/`). Name a
behaviour (`user-auth`), not a piece of work (`add-login-endpoint`).

## Requirement and criterion IDs

| ID | Form | Example |
|---|---|---|
| requirement | `REQ-<prefix>-NNN` | `REQ-LINK-001` |
| acceptance criterion | `AC-<prefix>-NNN.<n>` | `AC-LINK-001.3` |

- The prefix is the capability name in upper case (`billing:invoices` →
  `BILLING-INVOICES`) or its `prefix:` in the config. Two capabilities cannot
  share a prefix.
- The next free ID comes from `specworks spec show <capability>` (`nextId`),
  which also counts the IDs of other changes in flight. The agent never
  invents one.
- IDs are never reused: a removed ID stays in `requirements.md`'s History, so
  `nextId` skips it and `specworks check` rejects adding it again.

In a spec:

```markdown
### Requirement: REQ-LINK-002 Resolve a code

The system SHALL return the original URL for a code it issued, and reject a code it did not issue.

#### Scenario: AC-LINK-002.2 An unknown code is rejected

- **WHEN** `resolve("zzzzzz")` is called on an empty store
- **THEN** it raises `UnknownCode`
```

Rules `specworks check` enforces: SHALL or MUST in every requirement; at
least one `#### Scenario:` (exactly four hashes) per requirement, with
`- **WHEN**` and `- **THEN**` bullets (`- **GIVEN**` optional); criteria
numbered under their own requirement; a MODIFIED block repeats the whole
existing block; a REMOVED one has **Reason** and **Migration**.

## Tags

Tests and code point back to the spec with comments, in any language:

```python
# @ac AC-LINK-002.2
def test_ac_link_002_2_unknown_code_is_rejected(): ...

# @req REQ-LINK-001, REQ-LINK-003
def shorten(self, url: str, ttl: float | None = None) -> str: ...
```

```typescript
// @ac AC-LINK-002.2
it("AC-LINK-002.2 rejects an unknown code", ...)
```

- `@ac` goes above a **test**, `@req` above the **code** that implements a
  requirement (its entry point). One tag may list several IDs.
- A tag is **unknown** when its ID is in none of the change's specs (its delta,
  the living spec, or another active change's delta), or when no capability
  uses its prefix:

  ```text
  AC-LNK-002.2 at tests/test_store.py:28 (no capability uses the prefix LNK; did you mean LINK?)
  ```

## Which files are scanned

`test_globs` / `source_globs` in the config choose the files scanned for tags.
When they are empty, every file outside the workflow folder is scanned, except
docs (`.md`, `.rst`, `.txt`, ...), and a file is a **test file** when one of its
folders is `test`, `tests`, `__tests__` or `testing`, or its name looks like a
test (`test_x.py`, `x_test.go`, `x.test.ts`, `x.spec.ts`, `XTest.java`, ...).

In a glob `*` and `?` stay within one folder, `**` spans any number of folders
(`tests/**/*.py` includes `tests/test_x.py`; `src/*` does not include
`src/auth/x.py`, `src/**` does). Those are the only wildcards.

## The traceability matrix

`specworks trace` joins it all: requirement → criterion → tasks → tests
(`@ac`) → code (`@req`), and lists the gaps. Every gate uses the same
analysis.

```text
| Capability | Requirement | Acceptance criterion | Tasks | Tests | Code |
|---|---|---|---|---|---|
| links | REQ-LINK-001 Shorten a URL (ADDED) | AC-LINK-001.1 A valid URL gets a code | 1.1, 1.2, 1.3 | — | — |
...
## Gaps

- Acceptance criteria without a test (`@ac`): AC-LINK-001.1, ...
- Requirements without code (`@req`): REQ-LINK-001, REQ-LINK-002
```

During specify the Tests and Code columns are empty; the test and code phases
fill them. See [`specworks trace`](CLI-Specs#specworks-trace).
