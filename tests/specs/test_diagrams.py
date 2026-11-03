import pytest

from support.diagrams import CHANGE, make_change, make_fake_d2, run_json


@pytest.fixture
def fake_d2(tmp_path_factory, monkeypatch):
    return make_fake_d2(tmp_path_factory, monkeypatch)


@pytest.fixture
def change(tmp_path, monkeypatch):
    return make_change(tmp_path, monkeypatch)


# @ac AC-SPECS-014.1
def test_validate_reports_diagram_problems(change, fake_d2):
    (change / "diagrams/orphan.d2").write_text("a -> b\n")
    (change / "design.md").write_text((change / "design.md").read_text() + "![gone](diagrams/gone.svg)\n")
    code, data = run_json("check", "--change", CHANGE)
    issues = [(i["level"], i["message"]) for i in data["issues"]]
    assert ("error", "image diagrams/gone.svg does not exist") in issues
    assert any(level == "warning" and "has no SVG" in m for level, m in issues)
    assert any(level == "warning" and "not shown in design.md" in m and "orphan.svg" in m for level, m in issues)
