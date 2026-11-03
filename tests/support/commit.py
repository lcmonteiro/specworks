"""Helpers shared by the commit tests of several capabilities."""

import hashlib
import json

import pytest
from typer.testing import CliRunner

from helpers import REF as CLOSED_REF
from helpers import git, init_repo, make_planned_project, make_repo, on_a_branch
from specworks.cli import app
from specworks.core.changes import META_FILE, load_change
from specworks.core.config import load_config
from specworks.core.git import git_text

runner = CliRunner()
REF = "add-login"
CHANGE = f".specworks/changes/active/{REF}"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


def make_project(tmp_path, monkeypatch):
    """A project with the change `add-login` and `notes.txt`, `old.txt` and `src/a.py`, all committed on main; work goes on on `feature`."""
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    assert run_json("new", REF, "--no-branch")[0] == 0
    (tmp_path / "notes.txt").write_bytes(b"notes\n")
    (tmp_path / "old.txt").write_bytes(b"old\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_bytes(b"A = 1\n")
    on_a_branch(tmp_path, monkeypatch)
    return tmp_path


def change(root):
    return load_change(load_config(root), REF)


def record(root, **files):
    """Save the change's record as if the phase had started with exactly these files dirty (path -> content)."""
    ch = change(root)
    ch.dirty = {path.replace("__", "/"): sha(content) for path, content in files.items()}
    ch.save()
    git(root, "add", "--", f"{CHANGE}/{META_FILE}")
    git(root, "commit", "-q", "--allow-empty", "-m", "record")  # the change folder starts clean
    return change(root)


def head(root):
    return git_text(root, "rev-parse", "HEAD").strip()


def message(root):
    return git_text(root, "log", "-1", "--format=%B").strip()


def make_closed(tmp_path, monkeypatch):
    """The planned project's change `add-password-reset`, reviewed and then closed with `specworks close`: archived, its active folder gone."""
    root = make_repo(make_planned_project(tmp_path, monkeypatch), monkeypatch)
    active = root / ".specworks/changes/active" / CLOSED_REF
    (active / "review.md").write_text("# Review\n\n## Findings\n\nNone.\n", encoding="utf-8")
    assert run_json("phase", "review", "--change", CLOSED_REF)[0] == 0
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "review")  # the review phase is committed: what is dirty from here on is close's
    assert run_json("phase", "validate", "--change", CLOSED_REF)[0] == 0  # validate commits nothing: `.change.yaml` stays dirty
    assert run_json("phase", "close", "--change", CLOSED_REF)[0] == 0  # as `specworks start close` does, close's record names it
    assert f".specworks/changes/active/{CLOSED_REF}/{META_FILE}" in load_change(load_config(root), CLOSED_REF).dirty
    code, data = run_json("close", "--change", CLOSED_REF, "--base", "main")
    assert code == 0, data
    assert not active.exists()
    return root, data["archivedTo"]
