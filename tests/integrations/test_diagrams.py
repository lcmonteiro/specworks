import subprocess
import sys

import pyd2
import pytest

from helpers import fake_executable
from specworks.tools import diagrams as diagrams_module
from support.diagrams import CHANGE, FLOW, make_change, make_fake_d2, run_json, set_diagrams


@pytest.fixture
def fake_d2(tmp_path_factory, monkeypatch):
    return make_fake_d2(tmp_path_factory, monkeypatch)


@pytest.fixture
def change(tmp_path, monkeypatch):
    return make_change(tmp_path, monkeypatch)


# @ac AC-INTEG-001.1
def test_render_writes_stamped_svg_with_workspace_settings(change, fake_d2):
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 0, data
    assert [d["status"] for d in data["diagrams"]] == ["rendered"]
    svg = (change / "diagrams/reset-flow.svg").read_text()
    assert svg.startswith('<?xml version="1.0"?><!-- specworks:d2 sha256=')
    assert "--theme=0 --layout=elk --pad=24 --omit-version --dark-theme=200" in svg
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert code == 0 and data["diagrams"][0]["status"] == "ok"


# @ac AC-INTEG-002.1, AC-CLI-008.3
def test_editing_the_source_makes_the_svg_stale(change, fake_d2):
    run_json("diagrams", "--change", CHANGE)
    (change / "diagrams/reset-flow.d2").write_text(FLOW + "api -> mail: link\n")
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert code == 1 and data["diagrams"][0]["status"] == "stale"
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 0 and data["diagrams"][0]["status"] == "rendered"


# @ac AC-INTEG-002.2
def test_changing_the_theme_makes_the_svg_stale(change, fake_d2):
    run_json("diagrams", "--change", CHANGE)
    cfg = change.parents[3] / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("sketch: false", "sketch: true"))
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert data["diagrams"][0]["status"] == "stale"
    run_json("diagrams", "--change", CHANGE)
    assert "--sketch" in (change / "diagrams/reset-flow.svg").read_text()


# @ac AC-INTEG-002.3
def test_hand_edited_svg_is_stale(change, fake_d2):
    (change / "diagrams/reset-flow.svg").write_text("<svg></svg>")
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert data["diagrams"][0]["status"] == "stale"


@pytest.fixture
def no_d2(monkeypatch):
    """pyd2 has no binary (a broken install) and SPECWORKS_D2 is not set."""

    def missing():
        raise FileNotFoundError("the d2 binary is missing; reinstall pyd2")

    monkeypatch.delenv("SPECWORKS_D2", raising=False)
    monkeypatch.setattr(pyd2, "executable", missing)
    monkeypatch.setattr(sys.modules["pyd2.render"], "executable", missing)


# @ac AC-INTEG-002.5
def test_check_does_not_need_d2(change, no_d2):
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert code == 1 and data["diagrams"][0]["status"] == "missing"
    assert not (change / "diagrams/reset-flow.svg").exists()


# @ac AC-INTEG-003.2
def test_missing_d2_reports_pyd2s_error(change, no_d2):
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 1 and data["d2From"] == "missing" and data["d2"] is None
    assert data["diagrams"][0]["error"] == "cannot render reset-flow.d2: the d2 binary is missing; reinstall pyd2"


# @ac AC-INTEG-003.1
def test_specworks_d2_overrides_pyd2(monkeypatch):
    monkeypatch.delenv("SPECWORKS_D2", raising=False)
    assert diagrams_module.find_d2() == (pyd2.executable(), "pyd2")
    monkeypatch.setenv("SPECWORKS_D2", "/opt/d2")
    assert diagrams_module.find_d2() == ("/opt/d2", "SPECWORKS_D2")


# @ac AC-INTEG-003.2
def test_d2_that_does_not_run(change, monkeypatch):
    monkeypatch.setenv("SPECWORKS_D2", str(change / "no-such-d2"))
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 1 and data["diagrams"][0]["error"].startswith("cannot render reset-flow.d2: ")


# @ac AC-INTEG-003.1
def test_pyd2_provides_the_pinned_release(monkeypatch):
    monkeypatch.delenv("SPECWORKS_D2", raising=False)
    path, where = diagrams_module.find_d2()
    out = subprocess.run([path, "--version"], capture_output=True, text=True, check=True).stdout.strip()
    assert where == "pyd2" and out == pyd2.D2_VERSION


# @ac AC-INTEG-001.3
def test_render_args_are_stable():
    """The stamp hashes these flags: changing them would mark every committed SVG stale."""
    from specworks.core.config import DiagramSettings

    assert DiagramSettings().options().args() == [
        "--theme=0", "--layout=elk", "--pad=24", "--omit-version", "--dark-theme=200"
    ]
    assert DiagramSettings(dark_theme=None, sketch=True).options().args()[-1] == "--sketch"


# @ac AC-INTEG-003.3
def test_d2_errors_are_reported(change, fake_d2):
    (change / "diagrams/reset-flow.d2").write_text("BROKEN")
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 1 and "unexpected token" in data["diagrams"][0]["error"]


# @ac AC-INTEG-001.4
def test_real_d2_render(change):
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 0, data
    svg = (change / "diagrams/reset-flow.svg").read_text()
    assert "<!-- specworks:d2 sha256=" in svg and "</svg>" in svg and "Auth API" in svg


# @ac AC-INTEG-001.2, AC-PROJ-003.5
@pytest.mark.parametrize(
    "theme, dark, expected",
    [
        ("c4", "none", "--theme=303 --layout=elk --pad=24 --omit-version"),
        ("Colorblind Clear", "dark-flagship-terrastruct", "--theme=8 --layout=elk --pad=24 --omit-version --dark-theme=201"),
        ("4", "200", "--theme=4 --layout=elk --pad=24 --omit-version --dark-theme=200"),
        ("999", "null", "--theme=999 --layout=elk --pad=24 --omit-version"),
    ],
)
def test_theme_by_name_or_number(change, fake_d2, theme, dark, expected):
    set_diagrams(change, f"diagrams:\n  theme: {theme}\n  dark_theme: {dark}\n")
    code, data = run_json("diagrams", "--change", CHANGE)
    assert code == 0, data
    svg = (change / "diagrams/reset-flow.svg").read_text()
    assert expected + "</svg>" in svg


# @ac AC-INTEG-002.4
def test_renaming_a_theme_to_its_number_keeps_svgs_up_to_date(change, fake_d2):
    set_diagrams(change, "diagrams:\n  theme: c4\n")
    run_json("diagrams", "--change", CHANGE)
    set_diagrams(change, "diagrams:\n  theme: 303\n")
    code, data = run_json("diagrams", "--change", CHANGE, "--check")
    assert code == 0 and data["diagrams"][0]["status"] == "ok"


# @ac AC-INTEG-003.4
def test_an_svg_that_cannot_be_stamped_is_a_render_error(change, tmp_path_factory, monkeypatch):
    script = fake_executable(
        tmp_path_factory.mktemp("bin"),
        "d2",
        "import sys, pathlib\n"
        "src, out = pathlib.Path(sys.argv[-2]).read_text(), pathlib.Path(sys.argv[-1])\n"
        "if 'UNCLOSED' in src:\n    out.write_text('<?xml version=\"1.0\"<svg/>')\n"
        "elif 'LATIN' in src:\n    out.write_bytes(b'<svg>caf\\xe9</svg>')\n"
        "elif 'NOFILE' not in src:\n    out.write_text('<?xml version=\"1.0\"?><svg/>')\n",
    )
    monkeypatch.setenv("SPECWORKS_D2", str(script))
    for name in ("unclosed", "latin", "nofile"):
        (change / f"diagrams/{name}.d2").write_text(name.upper() + "\n")
    code, data = run_json("diagrams", "--change", CHANGE)
    result = {d["source"].rsplit("/", 1)[-1]: d for d in data["diagrams"]}
    assert code == 1 and result["reset-flow.d2"]["status"] == "rendered"
    for name in ("unclosed", "latin"):
        assert result[f"{name}.d2"]["status"] == "error" and result[f"{name}.d2"]["error"].startswith(f"cannot render {name}.d2: ")
    assert result["nofile.d2"]["status"] == "error" and "nofile.d2: no SVG was written" in result["nofile.d2"]["error"]
