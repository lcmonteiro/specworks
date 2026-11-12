"""
The harness tests need the ``harness`` extra (chatinho and deepagents, Python 3.12+): without it the folder is skipped.
"""

import importlib.util

import pytest

MISSING = [name for name in ("chatinho", "deepagents") if importlib.util.find_spec(name) is None]

if MISSING:
    # The test modules import the harness at the top, so without the extra they are not collected at all.
    collect_ignore_glob = ["test_*.py"]
else:
    from harness.scripted import make_project, new_change
    from specworks.core.workspace import load_workspace

    @pytest.fixture
    def project(tmp_path, monkeypatch):
        """
        A specworks project committed on `main`, checked out on the branch `add-x`, with no change yet.
        """
        return make_project(tmp_path, monkeypatch)

    @pytest.fixture
    def ws(project):
        return load_workspace(project)

    @pytest.fixture
    def module(ws):
        return ws.top

    @pytest.fixture
    def change(project):
        """
        The change `add-x` in phase refine, committed.
        """
        return new_change(project)
