import pytest

from specworks.cli import app
from support.diagrams import FLOW, make_change, make_fake_d2, run_json, runner, set_diagrams


@pytest.fixture
def fake_d2(tmp_path_factory, monkeypatch):
    return make_fake_d2(tmp_path_factory, monkeypatch)


@pytest.fixture
def change(tmp_path, monkeypatch):
    return make_change(tmp_path, monkeypatch)


# @ac AC-CLI-008.2, AC-PROJ-003.5
def test_list_themes_shows_the_one_in_use(change):
    set_diagrams(change, "diagrams:\n  theme: origami\n  dark_theme: none\n")
    code, data = run_json("diagrams", "--themes")
    assert code == 0 and data["theme"] == "origami" and data["darkTheme"] == "none"
    assert {"name": "c4", "id": 303, "dark": False} in data["themes"]
    assert {"name": "dark-mauve", "id": 200, "dark": True} in data["themes"]


# @ac AC-CLI-008.1
def test_diagrams_needs_change_or_themes(change):
    code, data = run_json("diagrams")
    assert code == 1 and "--change" in data["error"]



# @ac AC-CLI-008.5
def test_diagrams_refuses_a_folder_outside_the_workspace(change, tmp_path_factory):
    code, data = run_json("diagrams", "--dir", str(tmp_path_factory.mktemp("elsewhere")))
    assert code == 1 and "is outside the workspace" in data["error"]


# @ac AC-CLI-008.6
def test_diagrams_dir_is_relative_to_the_workspace_root(change, monkeypatch):
    root = change.parents[3]
    (root / "src/auth/docs/diagrams").mkdir(parents=True)
    (root / "src/auth/docs/diagrams/flow.d2").write_text(FLOW)
    assert runner.invoke(app, ["module", "add", "web"]).exit_code == 0
    monkeypatch.chdir(root / "web")
    code, data = run_json("diagrams", "--dir", "src/auth/docs", "--check")
    assert data["dir"] == "src/auth/docs"
    assert [d["source"] for d in data["diagrams"]] == ["src/auth/docs/diagrams/flow.d2"]


# @ac AC-CLI-008.7
def test_diagrams_refuses_a_folder_that_does_not_exist(change, fake_d2):
    code, data = run_json("diagrams", "--dir", "src/nope")
    assert code == 1 and "no folder" in data["error"] and "src/nope" in data["error"]
