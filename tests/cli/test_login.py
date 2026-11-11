"""`specworks login`: log in to GitHub Copilot for the harness, with the prompt on stderr and the result on stdout (REQ-CLI-023)."""

import json
import re
import subprocess
import sys
import textwrap

import pytest
from typer.testing import CliRunner

from specworks.cli import app

runner = CliRunner()
HARNESS_MODULES = ("chatinho", "deepagents")
OAUTH = "gho_secret"


def needs_the_extra():
    for name in (*HARNESS_MODULES, "httpx"):
        pytest.importorskip(name)


@pytest.fixture
def github(tmp_path, monkeypatch):
    """A fake GitHub behind every httpx request, a config folder in a temporary folder, and no real home."""
    needs_the_extra()
    from support.copilot import real_clock_github, route_httpx_to

    config = tmp_path / "config-home"
    for variable in ("XDG_CONFIG_HOME", "APPDATA", "HOME", "USERPROFILE"):
        monkeypatch.setenv(variable, str(config))
    fake = real_clock_github()
    route_httpx_to(monkeypatch, fake)
    return fake


@pytest.fixture
def folder(tmp_path, monkeypatch):
    """A folder that is not a project."""
    place = tmp_path / "elsewhere"
    place.mkdir()
    monkeypatch.chdir(place)
    return place


@pytest.fixture
def project(tmp_path, monkeypatch):
    from support.cli import make_project

    root = tmp_path / "project"
    root.mkdir()
    return make_project(root, monkeypatch)


def stored_login(scope="global", root=None):
    from specworks.harness.logins import LoginStore

    return LoginStore().load(scope, root)


def save_login(token=OAUTH):
    from specworks.harness.logins import Login, LoginStore

    LoginStore().save("global", None, Login(token))


def project_files(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if ".git" not in p.relative_to(root).parts)


# @ac AC-CLI-023.1
def test_ac_cli_023_1_a_global_login_by_default(github, folder):
    result = runner.invoke(app, ["login", "copilot", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {"provider": "copilot", "scope": "global", "reused": False}
    assert stored_login() is not None


# @ac AC-CLI-023.2
def test_ac_cli_023_2_a_local_login(github, project):
    from specworks.core.workspace import load_workspace

    before = project_files(project)
    result = runner.invoke(app, ["login", "copilot", "--local", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {"provider": "copilot", "scope": "local", "reused": False}
    assert project_files(project) == before, "the project's folder holds no new file"
    ws = load_workspace(project)
    assert stored_login("local", ws.root) is not None
    assert stored_login("global") is None


# @ac AC-CLI-023.3
def test_ac_cli_023_3_a_login_that_exists_is_reused(github, folder):
    github.valid.add(OAUTH)
    save_login()
    result = runner.invoke(app, ["login", "copilot", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {"provider": "copilot", "scope": "global", "reused": True}
    assert github.device_flows() == 0
    plain = runner.invoke(app, ["login", "copilot"])
    assert plain.exit_code == 0, plain.output
    assert len(plain.stdout.strip().splitlines()) == 1
    assert "reused" in plain.stdout.lower()
    assert github.device_flows() == 0


# @ac AC-CLI-023.4
def test_ac_cli_023_4_a_forced_login(github, folder):
    github.valid.add(OAUTH)
    save_login()
    result = runner.invoke(app, ["login", "copilot", "--force", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {"provider": "copilot", "scope": "global", "reused": False}
    assert github.device_flows() == 1
    stored = stored_login()
    assert stored is not None and stored.oauth_token == github.authorized[0]


# @ac AC-CLI-023.5
def test_ac_cli_023_5_the_prompt_on_stderr(github, folder):
    result = runner.invoke(app, ["login", "copilot", "--json"])
    assert result.exit_code == 0, result.output
    assert "https://github.com/login/device" in result.stderr
    assert "ABCD-1234" in result.stderr
    document = json.loads(result.stdout)  # stdout is one JSON document
    assert document["provider"] == "copilot"
    assert "ABCD-1234" not in result.stdout and "github.com" not in result.stdout


# @ac AC-CLI-023.6
def test_ac_cli_023_6_both_scopes(github, project):
    result = runner.invoke(app, ["login", "copilot", "--local", "--global"])
    assert result.exit_code == 2
    assert github.requests == []


# @ac AC-CLI-023.7
def test_ac_cli_023_7_local_needs_a_project(github, folder):
    result = runner.invoke(app, ["login", "copilot", "--local", "--json"])
    assert result.exit_code == 1
    document = json.loads(result.stdout)
    assert "error" in document and document["root"] is None
    assert github.requests == []


# @ac AC-CLI-023.8
def test_ac_cli_023_8_another_provider(github, folder):
    result = runner.invoke(app, ["login", "github"])
    assert result.exit_code == 1
    assert result.stderr.startswith("error: ")
    assert "copilot" in result.stderr
    assert github.requests == []


# @ac AC-CLI-023.9
def test_ac_cli_023_9_a_flow_that_fails(github, folder):
    github.valid.add(OAUTH)
    github.polls = ["denied"]
    save_login()
    result = runner.invoke(app, ["login", "copilot", "--force", "--json"])
    assert result.exit_code == 1
    assert "error" in json.loads(result.stdout)
    shown = result.stdout + result.stderr
    assert "gho_secret" not in shown and "tid=secret" not in shown
    stored = stored_login()
    assert stored is not None and stored.oauth_token == OAUTH, "the earlier login is as it was"


def forget_harness(monkeypatch):
    """Take the harness out of the imported modules, so the command imports it again."""
    for name in list(sys.modules):
        if name == "specworks.harness" or name.startswith("specworks.harness."):
            monkeypatch.delitem(sys.modules, name)


# @ac AC-CLI-023.10
def test_ac_cli_023_10_without_the_extra(tmp_path, monkeypatch):
    from support.cli import make_project

    make_project(tmp_path, monkeypatch)
    forget_harness(monkeypatch)
    for name in HARNESS_MODULES:
        monkeypatch.setitem(sys.modules, name, None)  # importing it raises ImportError, as when it is not installed
    result = runner.invoke(app, ["login", "copilot"])
    assert result.exit_code == 1
    assert "specworks[harness]" in result.stderr
    assert not re.search(r"\d+\.\d+", result.stderr)
    assert result.stderr.startswith("error: ")


# @ac AC-CLI-023.11
def test_ac_cli_023_11_other_commands_stay_light():
    code = textwrap.dedent(
        """
        import sys

        tried = []
        blocked = ("chatinho", "deepagents", "httpx")

        class Missing:
            # The harness extra is not installed: importing what login needs fails, and is recorded.
            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] in blocked:
                    tried.append(name)
                    raise ImportError(name)
                return None

        sys.meta_path.insert(0, Missing())
        import specworks
        from typer.testing import CliRunner
        from specworks.cli import app

        result = CliRunner().invoke(app, ["--help"])
        assert result.exit_code == 0, result.output
        assert "login" in result.output
        loaded = sorted(m for m in sys.modules if m.split(".")[0] in blocked or m.startswith("specworks.harness"))
        print("tried", tried, "loaded", loaded)
        """
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "tried [] loaded []"
