"""Close phase: capability registration, delta merge into living specs, requirements index, archive."""

import json
import re
import sys

import pytest
from typer.testing import CliRunner

from helpers import REF, fake_executable, run_json
from specworks.cli import app
from support.close_phase import CHANGE_DIR, make_ready, snapshot

runner = CliRunner()


@pytest.fixture
def ready(repo):
    return make_ready(repo)


# @ac AC-CLI-007.1
def test_dry_run_shows_the_plan_and_writes_nothing(ready):
    before = snapshot(ready)
    code, data = run_json("close", "--change", REF, "--base", "main", "--dry-run")
    assert code == 0, data
    assert data["merges"] == [
        {
            "capability": "user-auth",
            "spec": "src/auth/docs/spec.md",
            "requirements": "src/auth/docs/requirements.md",
            "created": False,
            "added": ["REQ-AUTH-003"],
            "modified": ["REQ-AUTH-002"],
            "removed": [],
        }
    ]
    assert data["archivedTo"] is None and snapshot(ready) == before


# @ac AC-CLI-007.2
def test_close_without_dry_run_refuses_no_run(ready):
    # The real close is the last check before the living docs change: it never skips the commands.
    before = snapshot(ready)
    code, data = run_json("close", "--change", REF, "--base", "main", "--no-run")
    assert code == 1 and "--no-run only goes with --dry-run" in data["error"]
    assert snapshot(ready) == before
    code, data = run_json("close", "--change", REF, "--base", "main", "--dry-run", "--no-run")
    assert code == 0, data


# @ac AC-CLI-007.3
def test_close_refuses_when_verify_fails(repo):
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 1 and "does not pass validate" in data["error"] and "/specworks-review" in data["goBackTo"]
    assert (repo / CHANGE_DIR).is_dir()


@pytest.fixture
def no_architecture(ready, tmp_path_factory):
    """The ready change with its module's `docs/architecture.md` removed, and a test command that counts its runs outside the repo."""
    (ready / "docs/architecture.md").unlink()
    counter = tmp_path_factory.mktemp("runs") / "count"
    counter.write_text("")
    command = f'"{sys.executable}" -c "open(r\'{counter}\', \'a\').write(\'x\')"'
    cfg = ready / ".specworks/config.yml"
    cfg.write_text(re.sub(r"(?m)^  test:.*$", lambda _: f"  test: {json.dumps(command)}", cfg.read_text(encoding="utf-8"), count=1), encoding="utf-8")
    return ready, counter


# @ac AC-CLI-007.4
def test_ac_cli_007_4_close_refuses_a_module_without_its_architecture(no_architecture):
    root, counter = no_architecture
    before = snapshot(root)
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 1
    assert data["error"] == f"{REF} has no docs/architecture.md: write the module's architecture before close (/specworks-close)"
    assert snapshot(root) == before  # nothing written
    assert counter.read_text() == ""  # refused before validate: no command ran
    assert (root / CHANGE_DIR).is_dir()
    code, data = run_json("list")
    assert [c["name"] for c in data["changes"]] == [REF]


# @ac AC-CLI-007.4
def test_ac_cli_007_4_the_dry_run_names_the_missing_architecture(no_architecture):
    root, _ = no_architecture
    before = snapshot(root)
    code, data = run_json("close", "--change", REF, "--base", "main", "--dry-run")
    assert code == 0, data
    assert [m["capability"] for m in data["merges"]] == ["user-auth"]  # the merge plan, as before
    assert data["missing"] == ["docs/architecture.md"]
    result = runner.invoke(app, ["close", "--change", REF, "--base", "main", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "missing: docs/architecture.md (write it before close)" in result.output
    assert snapshot(root) == before


# @ac AC-CLI-007.4
def test_ac_cli_007_4_the_dry_run_names_nothing_missing_with_the_architecture(ready):
    code, data = run_json("close", "--change", REF, "--base", "main", "--dry-run")
    assert code == 0, data
    assert data["missing"] == []
    result = runner.invoke(app, ["close", "--change", REF, "--base", "main", "--dry-run"])
    assert "missing:" not in result.output


# @ac AC-CLI-005.5
def test_capability_add_in_a_module(ready, monkeypatch):
    runner.invoke(app, ["module", "add", "services/billing"])
    code, data = run_json("capability", "add", "invoices", "--path", "src/invoices", "--module", "billing", "--prefix", "INV")
    assert code == 0 and data["ref"] == "billing:invoices" and data["codePath"] == "services/billing/src/invoices"
    assert data["prefix"] == "INV" and data["nextId"] == "REQ-INV-001"
    assert "invoices:" in (ready / "services/billing/.specworks/config.yml").read_text()


# @ac AC-CLI-008.4
def test_diagrams_in_a_docs_folder(ready, monkeypatch):
    script = fake_executable(ready, "d2", "import sys, pathlib\npathlib.Path(sys.argv[-1]).write_text('<?xml version=\"1.0\"?><svg/>')\n")
    monkeypatch.setenv("SPECWORKS_D2", str(script))
    folder = ready / "src/auth/docs/diagrams"
    folder.mkdir(parents=True)
    (folder / "reset.d2").write_text("a -> b\n")
    code, data = run_json("diagrams", "--dir", "src/auth/docs")
    assert code == 0 and data["dir"] == "src/auth/docs" and data["diagrams"][0]["status"] == "rendered"
    code, data = run_json("diagrams")
    assert code == 1 and "--change" in data["error"]


# @ac AC-CLI-005.4
def test_capability_add_rejects_a_prefix_already_in_use(ready):
    cfg = ready / ".specworks/config.yml"
    before = cfg.read_text()
    code, data = run_json("capability", "add", "login", "--path", "src/login", "--prefix", "AUTH")
    assert code == 1 and "AUTH is already used by user-auth" in data["error"]
    code, data = run_json("capability", "add", "auth", "--path", "src/login")  # derives AUTH too
    assert code == 1 and "AUTH is already used by user-auth" in data["error"]
    assert cfg.read_text() == before
