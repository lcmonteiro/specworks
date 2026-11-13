"""
The trace of a closed change: its matrix from the current tags, and the locations changed since its close.
"""

import pytest

import helpers
from helpers import REF, git, remove_repo, runner
from specworks.cli import app
from specworks.core.changes import archived_as
from specworks.core.config import load_config
from specworks.core.git import git_text
from specworks.core.workspace import load_workspace
from specworks.specs.capabilities import resolve_ref
from specworks.specs.trace import changed_since_close, living_spec_at
from support.commit import make_closed, run_json
from support.reopen import commit_all


@pytest.fixture
def closed(tmp_path, monkeypatch):
    """
    The planned project's change, closed with `specworks close` and the close committed; the close commit's hash.
    """
    root, _ = make_closed(tmp_path, monkeypatch)
    commit_all(root, "close")
    return root, git_text(root, "rev-parse", "HEAD").strip()


def archived(root):
    found = archived_as(load_config(root), REF)
    assert found is not None
    return found


def trace():
    code, data = run_json("trace", "--change", REF)
    assert code == 0, data
    return data, {r["ac"]: r for r in data["rows"]}


# @ac AC-SPECS-018.1
def test_ac_specs_018_1_a_closed_change_links_its_current_tests_and_code(closed):
    root, _ = closed
    (root / "tests/test_more.py").write_text("# @ac AC-AUTH-003.2\ndef test_more(): ...\n", encoding="utf-8")  # specworks: ignore-tags
    commit_all(root, "a test added after the close")
    data, rows = trace()
    assert rows["AC-AUTH-003.1"]["tests"] == ["tests/test_reset.py:1"] and rows["AC-AUTH-003.1"]["code"] == ["src/auth/reset.py:1"]
    assert sorted(rows["AC-AUTH-003.2"]["tests"]) == ["tests/test_more.py:1", "tests/test_reset.py:5"]
    assert rows["AC-AUTH-002.1"]["tests"] == ["tests/test_reset.py:9"] and rows["AC-AUTH-002.1"]["code"] == ["src/auth/lockout.py:1"]
    assert data["gaps"]["acWithoutTests"] == [] and data["gaps"]["reqWithoutCode"] == []


# @ac AC-SPECS-018.2
def test_ac_specs_018_2_locations_changed_since_the_close_are_marked(closed):
    root, close_commit = closed
    (root / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\ndef reset(): return 1\n", encoding="utf-8")  # specworks: ignore-tags
    commit_all(root, "a later fix")
    since = changed_since_close(load_workspace(root), archived(root))
    assert since.commit == close_commit and "src/auth/reset.py" in since.files, since
    assert "src/auth/lockout.py" not in since.files and "tests/test_reset.py" not in since.files, since

    data, rows = trace()
    assert rows["AC-AUTH-003.1"]["changed"] == ["src/auth/reset.py:1"]
    assert rows["AC-AUTH-003.2"]["changed"] == ["src/auth/reset.py:1"]
    assert rows["AC-AUTH-002.1"]["changed"] == []
    assert data["changedSinceClose"]["commit"] == close_commit and "src/auth/reset.py" in data["changedSinceClose"]["files"], data["changedSinceClose"]
    text = runner.invoke(app, ["trace", "--change", REF]).output
    assert "`src/auth/reset.py:1` (changed since close)" in text, text
    assert "`src/auth/lockout.py:1`" in text and "`src/auth/lockout.py:1` (changed since close)" not in text, text
    assert "`tests/test_reset.py:1`" in text and "`tests/test_reset.py:1` (changed since close)" not in text, text


# @ac AC-SPECS-018.2
def test_ac_specs_018_2_nothing_changed_since_the_close(closed):
    root, close_commit = closed
    since = changed_since_close(load_workspace(root), archived(root))
    assert since.commit == close_commit and since.files == frozenset(), since
    data, rows = trace()
    assert all(r["changed"] == [] for r in rows.values()), rows


# @ac AC-SPECS-018.3
def test_ac_specs_018_3_outside_git_nothing_is_marked(closed):
    root, _ = closed
    (root / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\ndef reset(): return 1\n", encoding="utf-8")  # specworks: ignore-tags
    remove_repo(root)
    since = changed_since_close(load_workspace(root), archived(root))
    assert since.commit is None and since.files == frozenset() and since.note, since
    data, rows = trace()
    assert all(r["changed"] == [] for r in rows.values()), rows
    assert set(data["changedSinceClose"]) == {"note"} and data["changedSinceClose"]["note"], data["changedSinceClose"]
    assert rows["AC-AUTH-003.1"]["code"] == ["src/auth/reset.py:1"]  # the trace itself is still given


# @ac AC-SPECS-018.3
def test_ac_specs_018_3_without_the_close_commit_nothing_is_marked(tmp_path, monkeypatch):
    root, _ = make_closed(tmp_path, monkeypatch)  # closed, but the close is not committed: no commit added the archive folder
    git(root, "status")  # still a git repository: only the close commit is missing
    since = changed_since_close(load_workspace(root), archived(root))
    assert since.commit is None and since.files == frozenset() and since.note, since
    data, rows = trace()
    assert all(r["changed"] == [] for r in rows.values()), rows
    assert set(data["changedSinceClose"]) == {"note"} and data["changedSinceClose"]["note"], data["changedSinceClose"]


# The living spec before the change: REQ-AUTH-002 has a second criterion, which the change's MODIFIED block
# (AC-AUTH-002.1 only) leaves out, so it goes with the block at close.
LIVING_WITH_002_2 = helpers.LIVING + """
#### Scenario: AC-AUTH-002.2 Locked account
- **WHEN** a locked account submits the right password
- **THEN** it is still refused
"""

LATER_002_3 = """
#### Scenario: AC-AUTH-002.3 Unlock by email
- **WHEN** a locked user opens the unlock link
- **THEN** the account is unlocked
"""


@pytest.fixture
def left_out(tmp_path, monkeypatch):
    """
    A closed change whose MODIFIED REQ-AUTH-002 leaves out AC-AUTH-002.2, still tagged in a test; the close committed.
    """
    monkeypatch.setattr(helpers, "LIVING", LIVING_WITH_002_2)
    root, _ = make_closed(tmp_path, monkeypatch)
    (root / "tests/test_left_out.py").write_text("# @ac AC-AUTH-002.2\ndef test_left_out(): ...\n", encoding="utf-8")  # specworks: ignore-tags
    commit_all(root, "close")
    return root


def add_later_criterion(root):
    """
    A later change adds AC-AUTH-002.3 to the living spec and tags a test with it (not committed).
    """
    spec = root / "src/auth/docs/spec.md"
    living = spec.read_text(encoding="utf-8")
    assert "AC-AUTH-002.2" not in living  # the close took it out with the MODIFIED block
    block_end = living.index("### Requirement: REQ-AUTH-003")
    spec.write_text(living[:block_end] + LATER_002_3.lstrip("\n") + "\n" + living[block_end:], encoding="utf-8")
    (root / "tests/test_unlock.py").write_text("# @ac AC-AUTH-002.3\ndef test_unlock(): ...\n", encoding="utf-8")  # specworks: ignore-tags


# @ac AC-SPECS-018.4
def test_ac_specs_018_4_a_criterion_added_after_the_close_is_not_removed(left_out):
    root = left_out
    add_later_criterion(root)
    commit_all(root, "a later change adds AC-AUTH-002.3")
    data, _ = trace()
    removed = data["gaps"]["removedStillTagged"]
    assert "AC-AUTH-002.3" not in removed, data["gaps"]
    assert "AC-AUTH-002.2" in removed, data["gaps"]


# @ac AC-SPECS-018.5
def test_ac_specs_018_5_outside_git_no_criterion_is_removed(left_out):
    root = left_out
    add_later_criterion(root)
    commit_all(root, "a later change adds AC-AUTH-002.3")
    remove_repo(root)
    data, rows = trace()
    assert data["gaps"]["removedStillTagged"] == [], data["gaps"]
    assert all(r["section"] != "REMOVED" for r in rows.values()), rows
    assert rows["AC-AUTH-002.1"]["tests"] == ["tests/test_reset.py:9"]  # the rest of the trace is still given


# @ac AC-SPECS-018.5
def test_ac_specs_018_5_without_the_close_commit_no_criterion_is_removed(tmp_path, monkeypatch):
    monkeypatch.setattr(helpers, "LIVING", LIVING_WITH_002_2)
    root, _ = make_closed(tmp_path, monkeypatch)  # closed, but the close is not committed
    (root / "tests/test_left_out.py").write_text("# @ac AC-AUTH-002.2\ndef test_left_out(): ...\n", encoding="utf-8")  # specworks: ignore-tags
    add_later_criterion(root)
    data, _ = trace()
    assert data["gaps"]["removedStillTagged"] == [], data["gaps"]


# @ac AC-SPECS-018.5
def test_ac_specs_018_5_no_living_spec_without_the_commit(left_out):
    root = left_out
    ws = load_workspace(root)
    cap = resolve_ref(ws, "user-auth")
    assert living_spec_at(ws, archived(root), cap, None) is None
    commit = git_text(root, "rev-parse", "HEAD").strip()
    remove_repo(root)
    assert living_spec_at(load_workspace(root), archived(root), cap, commit) is None
