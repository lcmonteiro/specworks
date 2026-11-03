import pytest

from support.modules import make_workspace, run, run_json


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    return make_workspace(tmp_path, monkeypatch)


# @ac AC-INTEG-005.5, AC-CLI-003.2
def test_init_in_subfolder_links_to_parent(workspace):
    run("init", "libs/auth", "--name", "auth")
    assert "  auth: libs/auth\n" in (workspace / ".specworks/config.yml").read_text()
    assert not (workspace / "libs/auth/.claude").exists()  # skills stay at the workspace root
    code, data = run_json("module", "list")
    assert "auth" in [m["name"] for m in data["modules"]]
