"""docs/walkthrough.md, end to end: one change through every phase, from init to close.

Each step writes what the phase's skill has the agent write, then moves on with
`specworks start` (or the gate the skill runs), so a change in any gate or
command that breaks the documented flow fails here.
"""

import re
import subprocess
import sys
from datetime import date

from typer.testing import CliRunner

from specworks.cli import app

runner = CliRunner()
REF = "add-slugify"
C = f"spec/changes/{REF}"

PROPOSAL = """\
# Proposal: add-slugify

## Why

Article titles are turned into URLs by hand, and the results are inconsistent.

## What Changes

- New `slugify(title)` function that turns a title into a URL slug.

## Capabilities

### Modified Capabilities

- `slugify`: first requirements of the capability (registered, no living spec yet).
"""

SPEC = """\
# Spec Delta: slugify

## Purpose

Turn titles into URL slugs.

## ADDED Requirements

### Requirement: REQ-SLUG-001 Slugify a title

The system SHALL turn a title into a slug: lower case, words joined by single hyphens, other characters dropped.

#### Scenario: AC-SLUG-001.1 Words become a hyphenated slug

- **WHEN** `slugify("Hello,  World!")` is called
- **THEN** it returns `"hello-world"`

#### Scenario: AC-SLUG-001.2 A title with no words is rejected

- **WHEN** `slugify("  !! ")` is called
- **THEN** it raises `ValueError`
"""

TASKS = """\
# Tasks: add-slugify

## 1. Slugify

- [ ] 1.1 Add `slugify(title: str) -> str` as a stub in `src/textkit/slug.py` (REQ-SLUG-001); verify the existing tests pass
- [ ] 1.2 Write failing tests for AC-SLUG-001.1 and AC-SLUG-001.2 tagged `@ac`; verify they fail on the stub
- [ ] 1.3 Implement `slugify` (REQ-SLUG-001) tagged `@req`; verify the 1.2 tests pass
"""

DESIGN = """\
# Design: add-slugify

## Interfaces

- `src/textkit/slug.py`: `slugify(title: str) -> str`, raises `ValueError` when the title has no words (REQ-SLUG-001)
"""

STUB = '''\
def slugify(title: str) -> str:
    """Turn a title into a URL slug. Implements REQ-SLUG-001."""
    raise NotImplementedError
'''

TESTS = """\
import pytest

from textkit.slug import slugify


# @ac AC-SLUG-001.1
def test_words_become_a_hyphenated_slug():
    assert slugify("Hello,  World!") == "hello-world"


# @ac AC-SLUG-001.2
def test_a_title_with_no_words_is_rejected():
    with pytest.raises(ValueError):
        slugify("  !! ")
"""

CODE = '''\
import re


# @req REQ-SLUG-001
def slugify(title: str) -> str:
    """Turn a title into a URL slug. Implements REQ-SLUG-001."""
    words = re.findall(r"[a-z0-9]+", title.lower())
    if not words:
        raise ValueError(f"no words in {title!r}")
    return "-".join(words)
'''

REVIEW = """\
# Review: add-slugify

Base: `main`

## Findings

- [x] R1 **spec-gap** `slugify("Café")` drops the `é` and returns `caf`; the spec only says "other characters dropped" (`src/textkit/slug.py:7`)
  - **Decision**: accepted: transliteration is out of scope (proposal); agreed with the user

## Changed files without tags

None.
"""


def sw(*args, ok=True):
    result = runner.invoke(app, list(args))
    assert (result.exit_code == 0) == ok, result.output
    return result.output


def test_walkthrough(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for key in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(key, "t" if key.endswith("NAME") else "t@t")
    git = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)  # noqa: E731
    (tmp_path / "src/textkit").mkdir(parents=True)
    (tmp_path / "src/textkit/__init__.py").write_text("")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_package.py").write_text("def test_package_imports():\n    import textkit  # noqa: F401\n")
    (tmp_path / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")

    # Set up: config, test command, the capability, a baseline commit.
    sw("init", "--dir", "spec", "--no-skills")
    cfg = tmp_path / "spec.yml"
    test_command = f'"{sys.executable}" -m pytest -q -p no:cacheprovider --rootdir . tests'
    cfg.write_text(re.sub(r"(?m)^  test:$", lambda _: f"  test: PYTHONPATH=src {test_command}", cfg.read_text(), count=1))
    sw("capability", "add", "slugify", "--path", "src/textkit", "--prefix", "SLUG")
    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-qm", "baseline")
    sw("new", REF)

    # specify: proposal, delta spec with IDs from the CLI, tasks.
    assert "next: REQ-SLUG-001" in sw("spec", "show", "slugify")
    sw("start", "specify", "--change", REF)
    (tmp_path / C / "proposal.md").write_text(PROPOSAL)
    (tmp_path / C / "specs/slugify").mkdir(parents=True)
    (tmp_path / C / "specs/slugify/spec.md").write_text(SPEC)
    (tmp_path / C / "tasks.md").write_text(TASKS)
    assert "valid (0 errors, 0 warnings)" in sw("check", "--change", REF)

    # design: the agreed API and its stub.
    sw("start", "design", "--change", REF)
    (tmp_path / C / "design.md").write_text(DESIGN)
    (tmp_path / "src/textkit/slug.py").write_text(STUB)
    sw("task", "done", "1.1", "--change", REF)
    sw("gate", "design", "--change", REF)

    # test: failing tests tagged @ac, red for the right reason.
    sw("start", "test", "--change", REF)
    (tmp_path / "tests/test_slug.py").write_text(TESTS)
    assert "NotImplementedError" in sw("run", "test", "--change", REF, "--json", ok=False)
    sw("task", "done", "1.2", "--change", REF)
    sw("gate", "test", "--change", REF)

    # code: the implementation, tagged @req; tests green.
    sw("start", "code", "--change", REF)
    (tmp_path / "src/textkit/slug.py").write_text(CODE)
    sw("task", "done", "1.3", "--change", REF)
    sw("gate", "code", "--change", REF)

    # review: no drift candidates; one finding from reading the code, accepted.
    started = sw("start", "review", "--change", REF)
    assert "same code as the run at" in started  # gate code's run is reused
    assert "0 drift candidates" in sw("review", "--change", REF, "--base", "main")
    (tmp_path / C / "review.md").write_text(REVIEW)
    sw("gate", "review", "--change", REF, "--base", "main")

    # validate and close.
    sw("phase", REF, "validate")
    assert "PASS" in sw("validate", "--change", REF, "--base", "main")
    assert "(new): ADDED REQ-SLUG-001" in sw("close", "--change", REF, "--base", "main", "--dry-run")
    closed = sw("close", "--change", REF, "--base", "main")
    assert f"archived -> spec/changes/archive/{date.today().isoformat()}-{REF}" in closed
    living = (tmp_path / "src/textkit/docs/spec.md").read_text()
    assert "### Requirement: REQ-SLUG-001 Slugify a title" in living and "## Purpose\n\nTurn titles into URL slugs." in living
    assert "| REQ-SLUG-001 | Slugify a title | AC-SLUG-001.1, AC-SLUG-001.2 |" in (tmp_path / "src/textkit/docs/requirements.md").read_text()
