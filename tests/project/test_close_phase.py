"""Close phase: capability registration, delta merge into living specs, requirements index, archive."""

import pytest

from helpers import REF, run_json
from specworks.specs.specfile import parse_spec
from support.close_phase import CHANGE_DIR, make_ready


@pytest.fixture
def ready(repo):
    return make_ready(repo)


# @ac AC-PROJ-008.2
def test_new_capability_must_be_registered_first(ready):
    delta = ready / CHANGE_DIR / "specs/audit-log/spec.md"
    delta.parent.mkdir(parents=True)
    delta.write_text(
        "## Purpose\n\nRecords security events for audits.\n\n## ADDED Requirements\n\n"
        "### Requirement: REQ-AUDIT-LOG-001 Log resets\nThe system SHALL log every password reset.\n\n"
        "#### Scenario: AC-AUDIT-LOG-001.1 Reset logged\n- **WHEN** a reset is requested\n- **THEN** an audit event is stored\n"
    )
    (ready / "tests/test_audit.py").write_text("# @ac AC-AUDIT-LOG-001.1\n")  # specworks: ignore-tags
    (ready / "src/audit").mkdir()
    (ready / "src/audit/log.py").write_text("# @req REQ-AUDIT-LOG-001\n")  # specworks: ignore-tags
    tasks = ready / CHANGE_DIR / "tasks.md"
    tasks.write_text(tasks.read_text() + "- [x] 2.2 Log resets (AC-AUDIT-LOG-001.1)\n")
    review = ready / CHANGE_DIR / "review.md"
    review.write_text(review.read_text() + "\n## Changed files without tags\n\nNone.\n")

    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 1 and data["error"].startswith("new capabilities must be registered before closing: audit-log")
    assert (ready / CHANGE_DIR).is_dir()

    code, data = run_json("capability", "add", "audit-log", "--path", "src/audit", "--description", "Security audit trail")
    assert code == 0 and data["ref"] == "audit-log" and data["new"] is False and data["prefix"] == "AUDIT-LOG"
    assert "  audit-log:\n    path: src/audit\n    description: \"Security audit trail\"\n" in (ready / ".specworks/config.yml").read_text()

    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 0, data
    text = (ready / "src/audit/docs/spec.md").read_text()
    assert text.startswith("# audit-log\n\n## Purpose\n\nRecords security events for audits.\n")
    assert [r.id for r in parse_spec(text).requirements] == ["REQ-AUDIT-LOG-001"]


# @ac AC-PROJ-003.1, AC-PROJ-004.4, AC-PROJ-008.3
def test_capability_add_validates(ready):
    code, data = run_json("capability", "add", "user-auth", "--path", "src/x")
    assert code == 1 and "already exists" in data["error"]
    code, data = run_json("capability", "add", "Bad_Name", "--path", "src/x")
    assert code == 1 and "kebab-case" in data["error"]
    code, data = run_json("capability", "add", "ok-name", "--path", "../out")
    assert code == 1


# @ac AC-PROJ-008.4
def test_capability_add_never_drops_existing_capabilities(project):
    # A flow mapping is not a block the text edit can extend; appending a second
    # `capabilities:` would make YAML keep only the new entry.
    cfg = project / ".specworks/config.yml"
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
