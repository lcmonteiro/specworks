"""Shared helpers for tests that need a planned change (proposal, delta spec and tasks)."""

import json
import os
import re
import shutil
import stat
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from samples import DELTA, LIVING, PROPOSAL, TASKS
from specworks.cli import app

runner = CliRunner()
REF = "add-password-reset"


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        pytest.fail(result.output)


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def init_repo(root):
    """An empty git repository on `main`: a project must be inside one."""
    git(root, "init", "-q", "-b", "main")


def remove_repo(root):
    """Take the folder out of its repository, for the tests of behaviour without git."""

    def writable(func, path, _excinfo):
        os.chmod(path, stat.S_IWRITE)  # git's object files are read-only on Windows
        func(path)

    shutil.rmtree(root / ".git", onerror=writable)


def on_a_branch(root, monkeypatch):
    """Commit everything on `main` as the baseline and go on on a feature branch: files changed from here on are the change's."""
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "baseline")
    git(root, "checkout", "-q", "-b", "feature")


def make_planned_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    cfg = tmp_path / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("capabilities: {}", "capabilities:\n  user-auth:\n    path: src/auth\n    prefix: AUTH"))
    (tmp_path / "src/auth/docs").mkdir(parents=True)
    (tmp_path / "src/auth/docs/spec.md").write_text(LIVING)
    run_json("new", REF, "--no-branch")  # stay on main
    change = tmp_path / ".specworks/changes/active" / REF
    (change / "proposal.md").write_text(PROPOSAL)
    (change / "specs/user-auth").mkdir(parents=True)
    (change / "specs/user-auth/spec.md").write_text(DELTA)
    (change / "tasks.md").write_text(TASKS)
    return tmp_path


def write_tests(root, *acs):
    (root / "tests").mkdir(exist_ok=True)
    body = "".join(f"# @ac {ac}\ndef test_{ac.lower().replace('-', '_').replace('.', '_')}():\n    assert False\n\n" for ac in acs)
    (root / "tests/test_reset.py").write_text(body)


PASS = f'"{sys.executable}" -c "print(\'ok\')"'


def make_repo(project, monkeypatch):
    """The planned project as a git repo: baseline on main, the change's work on a feature branch."""
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)
    cfg = project / ".specworks/config.yml"
    cfg.write_text(re.sub(r"(?m)^  test:.*$", lambda _: f"  test: {json.dumps(PASS)}", cfg.read_text(), count=1))
    (project / "src/auth/session.py").write_text("def session(): ...\n")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "baseline")
    git(project, "checkout", "-q", "-b", "feature")
    write_tests(project, "AC-AUTH-003.1", "AC-AUTH-003.2", "AC-AUTH-002.1")
    (project / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\ndef reset(): ...\n")  # specworks: ignore-tags
    (project / "src/auth/lockout.py").write_text("# @req REQ-AUTH-002\nLIMIT = 3\n")  # specworks: ignore-tags
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "implement")
    run_json("task", "done", "1.1", "1.2", "--change", REF)
    return project


def fake_executable(folder, name, script):
    """A program ``folder/name`` that runs the Python ``script`` with this interpreter, on any OS.

    POSIX runs a shebang file; Windows does not, so there it is a ``name.cmd`` wrapper.
    """
    source = folder / f"{name}.py"
    source.write_text(script)
    if os.name == "nt":
        program = folder / f"{name}.cmd"
        program.write_text(f'@"{sys.executable}" "{source}" %*\r\n@exit /b %errorlevel%\r\n')
    else:
        program = folder / name
        program.write_text(f"#!{sys.executable}\n" + script)
        program.chmod(program.stat().st_mode | stat.S_IEXEC)
    return program
