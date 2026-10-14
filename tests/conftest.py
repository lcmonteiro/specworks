import pytest
from helpers import make_planned_project


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A project with user-auth and a planned change; test modules may define their own `project`."""
    return make_planned_project(tmp_path, monkeypatch)
