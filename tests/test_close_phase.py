"""Close phase: capability registration, delta merge into living specs, requirements index, archive."""

import hashlib
import shutil
from datetime import date

import pytest
from typer.testing import CliRunner

from helpers import REF, fake_executable, run_json
from specworks.cli import app
from specworks.core.changes import load_change
from specworks.core.workspace import load_workspace
from specworks.specs.check import collect
from specworks.specs.merge import MergeError, apply_delta, close_change, plan_merge
from specworks.specs.specfile import parse_spec

runner = CliRunner()
CHANGE_DIR = f"spec/changes/{REF}"


@pytest.fixture
def ready(repo):
    """A change that passes validate: implemented, reviewed, in the review phase."""
    (repo / CHANGE_DIR / "review.md").write_text("# Review\n\n## Findings\n\nNone.\n")
    run_json("phase", "review", "--change", REF)
    return repo


def snapshot(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


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


def test_close_merges_indexes_and_archives(ready):
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 0, data
    today = date.today().isoformat()
    assert data["archivedTo"] == f"spec/changes/archive/{today}-{REF}"

    living = parse_spec((ready / "src/auth/docs/spec.md").read_text())
    assert [(r.id, r.title) for r in living.requirements] == [
        ("REQ-AUTH-001", "Password login"),
        ("REQ-AUTH-002", "Lockout after failures"),
        ("REQ-AUTH-003", "Password reset"),
    ]
    assert "3 failed attempts" in living.by_id()["REQ-AUTH-002"].description

    index = (ready / "src/auth/docs/requirements.md").read_text()
    assert "| REQ-AUTH-003 | Password reset | AC-AUTH-003.1, AC-AUTH-003.2 |" in index
    assert f"- {today} `{REF}`: ADDED REQ-AUTH-003; MODIFIED REQ-AUTH-002" in index

    archived = ready / data["archivedTo"]
    assert (archived / "proposal.md").is_file() and "phase: done" in (archived / ".change.yaml").read_text()
    assert not (ready / CHANGE_DIR).exists()
    code, data = run_json("list")
    assert data["changes"] == []
    code, data = run_json("spec", "show", "user-auth")
    assert data["nextId"] == "REQ-AUTH-004"


def test_close_refuses_when_verify_fails(repo):
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 1 and "does not pass validate" in data["error"] and "/specworks-review" in data["goBackTo"]
    assert (repo / CHANGE_DIR).is_dir()


def test_new_capability_must_be_registered_first(ready):
    delta = ready / CHANGE_DIR / "specs/audit-log/spec.md"
    delta.parent.mkdir(parents=True)
    delta.write_text(
        "## Purpose\n\nRecords security events for audits.\n\n## ADDED Requirements\n\n"
        "### Requirement: REQ-AUDIT-LOG-001 Log resets\nThe system SHALL log every password reset.\n\n"
        "#### Scenario: AC-AUDIT-LOG-001.1 Reset logged\n- **WHEN** a reset is requested\n- **THEN** an audit event is stored\n"
    )
    (ready / "tests/test_audit.py").write_text("# @ac AC-AUDIT-LOG-001.1\n")
    (ready / "src/audit").mkdir()
    (ready / "src/audit/log.py").write_text("# @req REQ-AUDIT-LOG-001\n")
    tasks = ready / CHANGE_DIR / "tasks.md"
    tasks.write_text(tasks.read_text() + "- [x] 2.2 Log resets (AC-AUDIT-LOG-001.1)\n")
    review = ready / CHANGE_DIR / "review.md"
    review.write_text(review.read_text() + "\n## Changed files without tags\n\nNone.\n")

    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 1 and data["error"].startswith("new capabilities must be registered before closing: audit-log")
    assert (ready / CHANGE_DIR).is_dir()

    code, data = run_json("capability", "add", "audit-log", "--path", "src/audit", "--description", "Security audit trail")
    assert code == 0 and data["ref"] == "audit-log" and data["new"] is False and data["prefix"] == "AUDIT-LOG"
    assert "  audit-log:\n    path: src/audit\n    description: \"Security audit trail\"\n" in (ready / "spec.yml").read_text()

    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 0, data
    text = (ready / "src/audit/docs/spec.md").read_text()
    assert text.startswith("# audit-log\n\n## Purpose\n\nRecords security events for audits.\n")
    assert [r.id for r in parse_spec(text).requirements] == ["REQ-AUDIT-LOG-001"]


def test_capability_add_validates(ready):
    code, data = run_json("capability", "add", "user-auth", "--path", "src/x")
    assert code == 1 and "already exists" in data["error"]
    code, data = run_json("capability", "add", "Bad_Name", "--path", "src/x")
    assert code == 1 and "kebab-case" in data["error"]
    code, data = run_json("capability", "add", "ok-name", "--path", "../out")
    assert code == 1


def test_capability_add_never_drops_existing_capabilities(project):
    # A flow mapping is not a block the text edit can extend; appending a second
    # `capabilities:` would make YAML keep only the new entry.
    cfg = project / "spec.yml"
    text = cfg.read_text()
    start = text.index("capabilities:\n  user-auth:")
    end = text.index("\n\n", start)
    cfg.write_text(text[:start] + "capabilities: {user-auth: {path: src/auth, prefix: AUTH}}" + text[end:])
    before = cfg.read_text()
    code, data = run_json("capability", "add", "billing", "--path", "src/billing")
    assert code == 1 and "add it by hand" in data["error"]
    assert cfg.read_text() == before
    code, data = run_json("spec", "list")
    assert [c["ref"] for c in data["capabilities"]] == ["user-auth"]


def test_capability_add_in_a_module(ready, monkeypatch):
    runner.invoke(app, ["module", "add", "services/billing"])
    code, data = run_json("capability", "add", "invoices", "--path", "src/invoices", "--module", "billing", "--prefix", "INV")
    assert code == 0 and data["ref"] == "billing:invoices" and data["codePath"] == "services/billing/src/invoices"
    assert data["prefix"] == "INV" and data["nextId"] == "REQ-INV-001"
    assert "invoices:" in (ready / "services/billing/spec.yml").read_text()


DELTA_MODIFY_MISSING = "## MODIFIED Requirements\n\n### Requirement: REQ-AUTH-009 Ghost\nThe system SHALL x.\n"


class FakeDelta:
    def __init__(self, text):
        self.doc = parse_spec(text)
        self.cap = type("Cap", (), {"ref": "user-auth"})()


@pytest.mark.parametrize(
    "delta, message",
    [
        (DELTA_MODIFY_MISSING, "REQ-AUTH-009 is MODIFIED but not in the living spec"),
        ("## REMOVED Requirements\n\n### Requirement: REQ-AUTH-009 Ghost\n", "REQ-AUTH-009 is REMOVED but not in the living spec"),
        ("## ADDED Requirements\n\n### Requirement: REQ-AUTH-001 Dup\nThe system SHALL x.\n", "REQ-AUTH-001 is ADDED but already"),
    ],
)
def test_merge_errors(delta, message):
    living = "# user-auth\n\n## Requirements\n\n### Requirement: REQ-AUTH-001 Login\nThe system SHALL log in.\n"
    with pytest.raises(MergeError, match=message):
        apply_delta(living, FakeDelta(delta))


def test_removed_requirement_is_deleted_and_other_sections_kept():
    living = (
        "# user-auth\n\nIntro.\n\n## Requirements\n\n### Requirement: REQ-AUTH-001 A\nThe system SHALL a.\n\n"
        "### Requirement: REQ-AUTH-002 B\nThe system SHALL b.\n\n## Notes\n\nKeep me.\n"
    )
    text, added, modified, removed = apply_delta(
        living, FakeDelta("## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 A\n**Reason**: x\n**Migration**: y\n")
    )
    assert removed == ["REQ-AUTH-001"] and "REQ-AUTH-001" not in text
    assert text.startswith("# user-auth\n\nIntro.\n") and text.endswith("## Notes\n\nKeep me.\n")


def test_headings_in_a_code_fence_are_text_when_merging():
    living = (
        "# user-auth\n\n## Requirements\n\n### Requirement: REQ-AUTH-001 A\nThe system SHALL read:\n\n"
        "```markdown\n## Example\n### Requirement: REQ-AUTH-009 not real\n```\n\n## Notes\n\nKeep me.\n"
    )
    text, added, _, removed = apply_delta(
        living,
        FakeDelta(
            "## ADDED Requirements\n\n### Requirement: REQ-AUTH-002 B\nThe system SHALL b.\n\n"
            "## REMOVED Requirements\n\n### Requirement: REQ-AUTH-001 A\n**Reason**: x\n**Migration**: y\n"
        ),
    )
    assert added == ["REQ-AUTH-002"] and removed == ["REQ-AUTH-001"]
    assert text == "# user-auth\n\n## Requirements\n\n### Requirement: REQ-AUTH-002 B\nThe system SHALL b.\n\n## Notes\n\nKeep me.\n"


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


def test_a_taken_archive_folder_fails_before_anything_is_written(ready):
    # e.g. a change with the same name was already closed today
    (ready / f"spec/changes/archive/{date.today().isoformat()}-{REF}").mkdir(parents=True)
    before = snapshot(ready)
    for extra in (["--dry-run"], []):
        code, data = run_json("close", "--change", REF, "--base", "main", *extra)
        assert code == 1 and "already exists" in data["error"]
    assert snapshot(ready) == before


def test_a_failed_archive_puts_the_living_docs_back(ready, monkeypatch):
    import shutil

    before = snapshot(ready)
    real_move, calls = shutil.move, []

    def move_failing_once(src, dst):
        calls.append(src)
        if len(calls) == 1:
            raise OSError("disk full")
        return real_move(src, dst)

    monkeypatch.setattr(shutil, "move", move_failing_once)
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 1 and "disk full" in data["error"]
    assert snapshot(ready) == before  # living spec, requirements.md and the change's phase untouched
    code, data = run_json("close", "--change", REF, "--base", "main")  # and closing again works
    assert code == 0, data


def test_a_removed_id_is_never_handed_out_again(project):
    shutil.rmtree(project / CHANGE_DIR)  # its delta takes REQ-AUTH-003; only the living spec counts here
    run_json("new", "drop-lockout")
    delta = project / "spec/changes/drop-lockout/specs/user-auth"
    delta.mkdir(parents=True)
    (delta / "spec.md").write_text("## REMOVED Requirements\n\n### Requirement: REQ-AUTH-002 Lockout\n**Reason**: x\n**Migration**: y\n")
    ws = load_workspace(project)
    change = load_change(ws.current.config, "drop-lockout")
    close_change(plan_merge(ws, change, collect(ws, change), "drop-lockout"), change, ws.current.config.archive_path)
    assert "REMOVED REQ-AUTH-002" in (project / "src/auth/docs/requirements.md").read_text()
    code, data = run_json("spec", "show", "user-auth")
    assert [r["id"] for r in data["requirements"]] == ["REQ-AUTH-001"] and data["nextId"] == "REQ-AUTH-003"


def test_capability_add_rejects_a_prefix_already_in_use(ready):
    cfg = ready / "spec.yml"
    before = cfg.read_text()
    code, data = run_json("capability", "add", "login", "--path", "src/login", "--prefix", "AUTH")
    assert code == 1 and "AUTH is already used by user-auth" in data["error"]
    code, data = run_json("capability", "add", "auth", "--path", "src/login")  # derives AUTH too
    assert code == 1 and "AUTH is already used by user-auth" in data["error"]
    assert cfg.read_text() == before
