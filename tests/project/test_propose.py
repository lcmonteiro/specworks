import re

import pytest

from samples import DELTA
from support.propose import make_change, make_project, run_json


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


@pytest.fixture
def change(project):
    return make_change(project)


# @ac AC-PROJ-010.1
def test_a_new_change_records_when_it_started(project):
    run_json("new", "other-change", "--no-branch")
    meta = (project / ".specworks/changes/active/other-change/.change.yaml").read_text()
    assert re.search(r"(?m)^created: '\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d'$", meta), meta


# @ac AC-PROJ-005.1
def test_two_capabilities_with_one_prefix_is_an_error(project):
    cfg = project / ".specworks/config.yml"
    cfg.write_text(cfg.read_text().replace("    prefix: AUTH\n", "    prefix: AUTH\n  login:\n    path: src/login\n    prefix: AUTH\n", 1))
    code, data = run_json("spec", "list")
    assert code == 1 and "user-auth and login both use the ID prefix AUTH" in data["error"]


# @ac AC-PROJ-015.1
def test_a_file_that_is_not_utf8_is_a_clear_error(change):
    (change / "specs/user-auth/spec.md").write_bytes(DELTA.encode().replace(b"single-use", b"single\xe9use"))
    code, data = run_json("check", "--change", "add-password-reset")
    assert code == 1 and "is not UTF-8 text" in data["error"] and "spec.md" in data["error"]
