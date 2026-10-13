import json
import os
import shutil
import stat
import sys

import pytest
from typer.testing import CliRunner

from specworks.cli import app

runner = CliRunner()
CHANGE = "add-reset"
FLOW = 'shape: sequence_diagram\nuser: User\napi: Auth API\nuser -> api: "POST /reset {email}"\n'


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    return result.exit_code, json.loads(result.output)


@pytest.fixture
def fake_d2(tmp_path_factory, monkeypatch):
    """A stand-in for d2 that records its arguments and writes a small SVG."""
    folder = tmp_path_factory.mktemp("bin")
    script = folder / "d2"
    script.write_text(
        f"#!{sys.executable}\n"
        "import sys, pathlib\n"
        "src, out = sys.argv[-2], sys.argv[-1]\n"
        "if 'BROKEN' in pathlib.Path(src).read_text():\n"
        "    print('err: failed to compile: unexpected token', file=sys.stderr); sys.exit(1)\n"
        "pathlib.Path(out).write_text('<?xml version=\"1.0\"?><svg viewBox=\"0 0 1 1\">' + ' '.join(sys.argv[1:-2]) + '</svg>')\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("SPECWORKS_D2", str(script))
    return script


@pytest.fixture
def change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", "--dir", "spec", "--no-skills"]).exit_code == 0
    run_json("new", CHANGE)
    path = tmp_path / "spec/changes" / CHANGE
    (path / "diagrams").mkdir()
    (path / "diagrams/reset-flow.d2").write_text(FLOW)
    (path / "design.md").write_text("# Design\n\n![Reset flow (REQ-AUTH-003)](diagrams/reset-flow.svg)\n")
    return path


def test_render_writes_stamped_svg_with_workspace_settings(change, fake_d2):
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 0, data
    assert [d["status"] for d in data["diagrams"]] == ["rendered"]
    svg = (change / "diagrams/reset-flow.svg").read_text()
    assert svg.startswith('<?xml version="1.0"?><!-- specworks:d2 sha256=')
    assert "--theme=0 --layout=elk --pad=24 --omit-version --dark-theme=200" in svg
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert code == 0 and data["diagrams"][0]["status"] == "ok"


def test_editing_the_source_makes_the_svg_stale(change, fake_d2):
    run_json("diagrams", "--change", CHANGE)
    (change / "diagrams/reset-flow.d2").write_text(FLOW + "api -> mail: link\n")
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert code == 1 and data["diagrams"][0]["status"] == "stale"
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 0 and data["diagrams"][0]["status"] == "rendered"


def test_changing_the_theme_makes_the_svg_stale(change, fake_d2):
    run_json("diagrams", "--change", CHANGE)
    cfg = change.parents[2] / "spec.yml"
    cfg.write_text(cfg.read_text().replace("sketch: false", "sketch: true"))
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert data["diagrams"][0]["status"] == "stale"
    run_json("diagrams", "--change", CHANGE)
    assert "--sketch" in (change / "diagrams/reset-flow.svg").read_text()


def test_hand_edited_svg_is_stale(change, fake_d2):
    (change / "diagrams/reset-flow.svg").write_text("<svg></svg>")
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert data["diagrams"][0]["status"] == "stale"


def test_check_does_not_need_d2(change, monkeypatch):
    monkeypatch.setenv("SPECWORKS_D2", "")
    monkeypatch.setenv("PATH", "")
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert code == 1 and data["diagrams"][0]["status"] == "missing"
    assert not (change / "diagrams/reset-flow.svg").exists()


def test_missing_d2_explains_how_to_install(change, monkeypatch):
    monkeypatch.setenv("SPECWORKS_D2", "")
    monkeypatch.setenv("PATH", "")
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 1
    assert "d2 is not installed" in data["diagrams"][0]["error"] and "d2lang.com" in data["diagrams"][0]["error"]


def test_d2_errors_are_reported(change, fake_d2):
    (change / "diagrams/reset-flow.d2").write_text("BROKEN")
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 1 and "unexpected token" in data["diagrams"][0]["error"]


def test_validate_reports_diagram_problems(change, fake_d2):
    (change / "diagrams/orphan.d2").write_text("a -> b\n")
    (change / "design.md").write_text((change / "design.md").read_text() + "![gone](diagrams/gone.svg)\n")
    code, data = run_json("validate", "--change", CHANGE)
    issues = [(i["level"], i["message"]) for i in data["issues"]]
    assert ("error", "image diagrams/gone.svg does not exist") in issues
    assert any(level == "warning" and "has no SVG" in m for level, m in issues)
    assert any(level == "warning" and "not shown in design.md" in m and "orphan.svg" in m for level, m in issues)


@pytest.mark.parametrize(
    "block, message",
    [("diagrams:\n  layout: circo\n", "elk or dagre"), ("diagrams:\n  colour: red\n", "unknown keys"), ("diagrams: dark\n", "mapping")],
)
def test_invalid_diagram_settings(change, block, message):
    cfg = change.parents[2] / "spec.yml"
    text = cfg.read_text()
    cfg.write_text(text[: text.index("diagrams:")] + block)
    code, data = run_json("context")
    assert code == 1 and message in data["error"]


def test_real_d2_render(change):
    if shutil.which("d2") is None and not os.environ.get("SPECWORKS_D2"):
        if os.environ.get("SPECWORKS_REQUIRE_D2"):
            pytest.fail("SPECWORKS_REQUIRE_D2 is set but d2 is not installed")
        pytest.skip("d2 is not installed")
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 0, data
    svg = (change / "diagrams/reset-flow.svg").read_text()
    assert "<!-- specworks:d2 sha256=" in svg and "</svg>" in svg and "Auth API" in svg
