"""`specworks harness`: the harness chat in the terminal, imported only by this command (REQ-CLI-022)."""

import re
import subprocess
import sys
import textwrap

import pytest
from typer.testing import CliRunner

from specworks.cli import app

runner = CliRunner()
HARNESS_MODULES = ("chatinho", "deepagents")


def needs_the_extra():
    for name in HARNESS_MODULES:
        pytest.importorskip(name)


@pytest.fixture
def harness_project(tmp_path, monkeypatch):
    needs_the_extra()
    from harness.scripted import make_project

    return make_project(tmp_path, monkeypatch)


def forget_harness(monkeypatch):
    """Take the harness out of the imported modules, so the command imports it again."""
    for name in list(sys.modules):
        if name == "specworks.harness" or name.startswith("specworks.harness."):
            monkeypatch.delitem(sys.modules, name)


# @ac AC-CLI-022.1
def test_ac_cli_022_1_without_the_extra(tmp_path, monkeypatch):
    from support.cli import make_project

    make_project(tmp_path, monkeypatch)
    forget_harness(monkeypatch)
    for name in HARNESS_MODULES:
        monkeypatch.setitem(sys.modules, name, None)  # importing it raises ImportError, as when it is not installed
    result = runner.invoke(app, ["harness"])
    assert result.exit_code == 1
    assert "specworks[harness]" in result.stderr
    assert "Python" not in result.stderr
    assert not re.search(r"\d+\.\d+", result.stderr)
    assert result.stderr.startswith("error: ")


# @ac AC-CLI-022.2
def test_ac_cli_022_2_no_key(harness_project, monkeypatch):
    import chatinho

    monkeypatch.delenv("SPECWORKS_MODEL_API_KEY", raising=False)
    monkeypatch.setenv("SPECWORKS_MODEL_MODEL", "gpt-test")
    opened = []
    monkeypatch.setattr(chatinho.ChatSession, "run", lambda self: opened.append(self))
    monkeypatch.setattr(chatinho.ChatSession, "start", lambda self: opened.append(self))
    result = runner.invoke(app, ["harness"])
    assert result.exit_code == 1
    assert "SPECWORKS_MODEL_API_KEY" in result.stderr
    assert result.stderr.startswith("error: ")
    assert opened == []


def opened_sessions(monkeypatch):
    """The sessions the command runs or starts, recorded instead of opening a terminal."""
    import chatinho

    opened = []
    monkeypatch.setattr(chatinho.ChatSession, "run", lambda self: opened.append(self))
    monkeypatch.setattr(chatinho.ChatSession, "start", lambda self: opened.append(self))
    return opened


# @ac AC-CLI-022.6
def test_ac_cli_022_6_the_chat_opens_with_nothing_said(harness_project, monkeypatch):
    from harness.scripted import ScriptedModel, chat, peer_id
    from specworks.core.workspace import load_workspace

    model = ScriptedModel(script={"refine": ["refining add x"]})
    session, user = chat(load_workspace(harness_project), model)
    assert user.messages() == [] and user.heard == []
    assert model.peers_run() == []
    # the user starts the change: `@refine add x`
    session, user = chat(load_workspace(harness_project), model, say="add x")
    assert model.peers_run() == ["refine"]
    first = user.messages()[0]
    assert first.text == "add x" and first.frm == 0 and first.to == peer_id(session, "refine")


# @ac AC-CLI-022.6
def test_ac_cli_022_6_the_command_says_nothing(harness_project, monkeypatch):
    import specworks.harness.session as session_module
    from harness.scripted import ScriptedModel

    monkeypatch.setattr(session_module, "model_from_env", lambda **_: ScriptedModel())
    opened = opened_sessions(monkeypatch)
    result = runner.invoke(app, ["harness"])
    assert result.exit_code == 0, result.output
    assert result.output == ""
    assert len(opened) == 1


# @ac AC-CLI-022.7
def test_ac_cli_022_7_no_change_option(harness_project, monkeypatch):
    opened = opened_sessions(monkeypatch)
    result = runner.invoke(app, ["harness", "--change", "add-x"])
    assert result.exit_code == 2
    assert "--change" in result.stderr
    assert opened == []


# @ac AC-CLI-022.5
def test_ac_cli_022_5_other_commands_stay_light():
    code = textwrap.dedent(
        """
        import sys

        tried = []

        class Missing:
            # The harness extra is not installed: importing chatinho or deepagents fails, and is recorded.
            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] in ("chatinho", "deepagents"):
                    tried.append(name)
                    raise ImportError(name)
                return None

        sys.meta_path.insert(0, Missing())
        import specworks
        from typer.testing import CliRunner
        from specworks.cli import app

        result = CliRunner().invoke(app, ["--help"])
        assert result.exit_code == 0, result.output
        assert "harness" in result.output
        loaded = sorted(m for m in sys.modules if m.split(".")[0] in ("chatinho", "deepagents"))
        print("tried", tried, "loaded", loaded)
        """
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "tried [] loaded []"
