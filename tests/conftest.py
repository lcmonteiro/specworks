import pytest

from helpers import make_planned_project, make_repo


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A project with user-auth and a planned change; test modules may define their own `project`."""
    return make_planned_project(tmp_path, monkeypatch)


@pytest.fixture
def repo(project, monkeypatch):
    """The planned project as a git repo: baseline on main, implemented on a feature branch, tests passing."""
    return make_repo(project, monkeypatch)
