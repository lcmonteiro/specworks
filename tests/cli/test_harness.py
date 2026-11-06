"""`specworks harness`: the harness chat in the terminal, imported only by this command (REQ-CLI-022)."""

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
    result = runner.invoke(app, ["harness", "add x"])
    assert result.exit_code == 1
    assert "specworks[harness]" in result.stderr
    assert "3.12" in result.stderr
    assert result.stderr.startswith("error: ")


# @ac AC-CLI-022.2
def test_ac_cli_022_2_no_key(harness_project, monkeypatch):
    import chatinho

    monkeypatch.delenv("SPECWORKS_MODEL_API_KEY", raising=False)
    monkeypatch.setenv("SPECWORKS_MODEL_MODEL", "gpt-test")
    opened = []
    monkeypatch.setattr(chatinho.ChatSession, "run", lambda self: opened.append(self))
    monkeypatch.setattr(chatinho.ChatSession, "start", lambda self: opened.append(self))
    result = runner.invoke(app, ["harness", "add x"])
    assert result.exit_code == 1
    assert "SPECWORKS_MODEL_API_KEY" in result.stderr
    assert result.stderr.startswith("error: ")
    assert opened == []


# @ac AC-CLI-022.3
def test_ac_cli_022_3_the_request_goes_to_refine(harness_project):
    from harness.scripted import ScriptedModel, chat, peer_id
    from specworks.core.workspace import load_workspace
    from specworks.harness.session import first_peer

    assert first_peer(None) == "refine"
    session, user = chat(load_workspace(harness_project), ScriptedModel(), request="add x")
    first = user.messages()[0]
    assert first.text == "add x" and first.frm == 0
    assert first.to == peer_id(session, "refine")


# @ac AC-CLI-022.4
def test_ac_cli_022_4_continuing_a_change(harness_project):
    from harness.scripted import ScriptedModel, User, chat, new_change, peer_id, write_chat
    from specworks.core.workspace import load_workspace
    from specworks.harness import build_harness
    from specworks.harness.session import first_peer

    change = new_change(harness_project, phase="design")
    ws = load_workspace(harness_project)
    assert first_peer(change) == "build"
    build = peer_id(build_harness(ws, ScriptedModel(), change=change, frontend=User()), "build")
    earlier = [
        {"id": "msg-00000000000000b1", "from": 0, "to": build, "replyTo": None, "status": "answered", "text": "build add-x", "at": "2026-11-01T10:00:00"},
        {"id": "msg-00000000000000b2", "from": build, "to": None, "replyTo": "msg-00000000000000b1", "status": "answered", "text": "design agreed", "at": "2026-11-01T10:00:05"},
    ]
    write_chat(change, earlier)
    session, user = chat(ws, ScriptedModel(), request="go on", change=change)
    texts = [m.text for m in user.messages()]
    assert texts[:2] == ["build add-x", "design agreed"]
    go_on = next(m for m in user.messages() if m.text == "go on")
    assert go_on.frm == 0 and go_on.to == peer_id(session, "build")


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
