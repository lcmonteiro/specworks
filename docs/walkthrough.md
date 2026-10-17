# Walkthrough: one change, start to finish

A small Python library, `textkit`, gains a `slugify` function. This page follows
the change through every phase: what each skill has the agent write, and the
CLI commands it runs, with their real output. In practice you type
`/specworks-specify`, `/specworks-design`, … and the agent does all of this; the
commands are shown so you can see what each step checks.

`tests/test_walkthrough.py` runs exactly this flow, so it stays true.
For every skill, command and gate check in depth, see the {doc}`tutorial <tutorial/index>` and the {doc}`CLI reference <cli/index>`.

## Set up

```bash
specworks init --dir spec --tools claude
specworks capability add slugify --path src/textkit --prefix SLUG --description "Turn titles into URL slugs"
```

`spec.yml` gets the project's test command (`commands.test: uv run pytest -q`).
The capability is the durable behaviour; its living docs will live in
`src/textkit/docs/`, next to the code.

## refine (optional)

A change this small skips refinement:

```
$ specworks new add-slugify
created spec/changes/add-slugify
```

## specify: what changes, and how it is checked

The agent asks the CLI where the delta spec goes and which ID comes next, never
inventing them:

```
$ specworks spec show slugify
slugify
  prefix:    REQ-SLUG-  next: REQ-SLUG-001
  delta:     specs/slugify/spec.md
  living:    src/textkit/docs/spec.md
```

It writes `proposal.md`, `tasks.md` and the delta spec
`specs/slugify/spec.md`, then confirms the requirement and its acceptance
criteria with you:

```markdown
## ADDED Requirements

### Requirement: REQ-SLUG-001 Slugify a title

The system SHALL turn a title into a slug: lower case, words joined by single hyphens, other characters dropped.

#### Scenario: AC-SLUG-001.1 Words become a hyphenated slug

- **WHEN** `slugify("Hello,  World!")` is called
- **THEN** it returns `"hello-world"`

#### Scenario: AC-SLUG-001.2 A title with no words is rejected

- **WHEN** `slugify("  !! ")` is called
- **THEN** it raises `ValueError`
```

```
$ specworks check --change add-slugify
add-slugify: valid (0 errors, 0 warnings)
```

## design: the API, as stubs

Each phase starts with `specworks start`, which moves the change only once the
gates behind it pass:

```
$ specworks start design --change add-slugify
gate specify:
[ok  ] specs and tasks are valid (specworks check)
[ok  ] tasks.md is written
[ok  ] every acceptance criterion has a task
add-slugify: phase specify → design
```

The API agreed with you goes under `## Interfaces` in `design.md`, and into the
code as a stub that only says "not implemented":

```markdown
- `src/textkit/slug.py`: `slugify(title: str) -> str`, raises `ValueError` when the title has no words (REQ-SLUG-001)
```

```
$ specworks gate design --change add-slugify
[ok  ] specs and tasks are valid (specworks check)
[ok  ] design.md has an Interfaces section (write "None" when the API does not change)
[ok  ] every file named under Interfaces exists
[ok  ] the existing tests still pass with the stubs (commands.test)
         $ uv run pytest -q  (in ., exit 0)
gate design: passed
```

## test: failing tests, one per criterion

Tests call the stub and carry an `@ac` tag naming the criterion they prove:

```python
# @ac AC-SLUG-001.1
def test_words_become_a_hyphenated_slug():
    assert slugify("Hello,  World!") == "hello-world"
```

They must fail for the right reason, the stub, not an import error:

```
$ specworks run test --change add-slugify
FAILED tests/test_slug.py::test_words_become_a_hyphenated_slug - NotImplement...
FAILED tests/test_slug.py::test_a_title_with_no_words_is_rejected - NotImplem...
2 failed, 1 passed in 0.02s
```

```
$ specworks gate test --change add-slugify
[ok  ] specs and tasks are valid (specworks check)
[ok  ] every acceptance criterion has a test (@ac tag in a test file)
[ok  ] no tag refers to an unknown requirement or criterion
[ok  ] @ac tags are in test files (configure test_globs if your tests live elsewhere)
[ok  ] removed requirements are no longer tagged
gate test: passed
```

## code: make them pass

The implementation replaces the stub and carries an `@req` tag; each task is
ticked with `specworks task done` once its check passes:

```python
# @req REQ-SLUG-001
def slugify(title: str) -> str:
    words = re.findall(r"[a-z0-9]+", title.lower())
    if not words:
        raise ValueError(f"no words in {title!r}")
    return "-".join(words)
```

```
$ specworks gate code --change add-slugify
[ok  ] specs and tasks are valid (specworks check)
[ok  ] every task is done (specworks task list --pending)
[ok  ] every requirement has code (@req tag)
[ok  ] every acceptance criterion still has a test (@ac tag)
[ok  ] no tag refers to an unknown requirement or criterion
[ok  ] removed requirements are gone from tests and code
[ok  ] the test suite passes (commands.test)
         $ uv run pytest -q  (in ., exit 0)
gate code: passed
```

## review: do code, spec and design agree?

`start review` runs `gate code` again; the code has not changed, so the test run
is reused rather than repeated:

```
$ specworks start review --change add-slugify
         $ uv run pytest -q  (in ., exit 0, same code as the run at 2026-10-15 16:21:18)
add-slugify: phase code → review
$ specworks review --change add-slugify --base main
...
0 drift candidates
```

The CLI finds no drift; reading the code finds one difference. `slugify("Café")`
returns `caf`. The proposal put transliteration out of scope, so with your
agreement the finding is accepted, and `review.md` records it:

```markdown
- [x] R1 **spec-gap** `slugify("Café")` drops the `é` and returns `caf`; the spec only says "other characters dropped" (`src/textkit/slug.py:7`)
  - **Decision**: accepted: transliteration is out of scope (proposal); agreed with the user
```

`specworks gate review --change add-slugify --base main` then passes.

## validate: ready to close?

A read-only report; every failure would name the phase that fixes it:

```
$ specworks validate --change add-slugify --base main
Completeness (5/5)
  ...
Correctness (6/6)
  ...
Coherence (3/3)
  ...
add-slugify: PASS (0 critical, 0 warnings)
```

## close: into the living docs

```
$ specworks close --change add-slugify --base main
merged slugify -> src/textkit/docs/spec.md (new): ADDED REQ-SLUG-001
archived -> spec/changes/archive/2026-10-15-add-slugify
```

`src/textkit/docs/spec.md` now holds REQ-SLUG-001 with its two criteria, and
`requirements.md` next to it indexes them, with a History line for
`add-slugify`. The next change to `slugify` starts from there.
