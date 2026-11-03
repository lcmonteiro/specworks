import pytest

from support.diagrams import make_change, run_json, set_diagrams


@pytest.fixture
def change(tmp_path, monkeypatch):
    return make_change(tmp_path, monkeypatch)


@pytest.mark.parametrize(
    "block, message",
    [("diagrams:\n  layout: circo\n", "elk or dagre"), ("diagrams:\n  colour: red\n", "unknown keys"), ("diagrams: dark\n", "mapping")],
)
def test_invalid_diagram_settings(change, block, message):
    cfg = change.parents[3] / ".specworks/config.yml"
    text = cfg.read_text()
    cfg.write_text(text[: text.index("diagrams:")] + block)
    code, data = run_json("context")
    assert code == 1 and message in data["error"]


def test_unknown_theme_name_lists_the_names(change):
    set_diagrams(change, "diagrams:\n  theme: rainbow\n")
    code, data = run_json("context")
    assert code == 1 and "unknown theme 'rainbow'" in data["error"] and "colorblind-clear" in data["error"]
