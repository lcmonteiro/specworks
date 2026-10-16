"""Gates reuse the result of a project command run on an identical working tree."""

import json
import re
import sys

import pytest

from helpers import REF, git, run_json

TESTS = "the test suite passes (commands.test)"


@pytest.fixture
def counted(repo, tmp_path_factory):
    """The repo with a test command that counts its runs in a file outside the repo (so counting changes nothing)."""
    counter = tmp_path_factory.mktemp("runs") / "count"
    counter.write_text("")
    command = f'"{sys.executable}" -c "open(r\'{counter}\', \'a\').write(\'x\')"'
    cfg = repo / "spec.yml"
    cfg.write_text(re.sub(r"(?m)^  test:.*$", lambda _: f"  test: {json.dumps(command)}", cfg.read_text(), count=1))
    return repo, counter


def gate_tests():
    code, data = run_json("gate", "code", "--change", REF)
    return next(c for c in data["checks"] if c["name"] == TESTS)


def runs(counter):
    return len(counter.read_text())


def test_same_tree_reuses_the_run(counted):
    repo, counter = counted
    first, second = gate_tests(), gate_tests()
    assert runs(counter) == 1
    assert "same code as the run at" not in first["details"][0] and "same code as the run at" in second["details"][0]
    assert first["ok"] == second["ok"]


def test_code_changes_rerun_but_workflow_files_do_not(counted):
    repo, counter = counted
    gate_tests()
    (repo / "spec/changes" / REF / "review.md").write_text("# Review\n")  # workflow folder: not part of the tree
    gate_tests()
    assert runs(counter) == 1
    (repo / "src/auth/reset.py").write_text("# @req REQ-AUTH-003\ndef reset(): return 1\n")  # tracked file changed
    gate_tests()
    assert runs(counter) == 2
    (repo / "src/auth/notes.py").write_text("a = 1\n")  # new untracked file
    gate_tests()
    (repo / "src/auth/notes.py").write_text("a = 2\n")  # its content counts, not only its name
    gate_tests()
    assert runs(counter) == 4


def test_a_failing_run_is_reused_too(counted, monkeypatch):
    repo, counter = counted
    cfg = repo / "spec.yml"
    fail = f'"{sys.executable}" -c "open(r\'{counter}\', \'a\').write(\'x\'); raise SystemExit(3)"'
    cfg.write_text(re.sub(r"(?m)^  test:.*$", lambda _: f"  test: {json.dumps(fail)}", cfg.read_text(), count=1))
    first, second = gate_tests(), gate_tests()
    assert runs(counter) == 1 and not first["ok"] and not second["ok"] and "exit 3" in second["details"][0]


def test_cache_can_be_turned_off(counted, monkeypatch):
    repo, counter = counted
    monkeypatch.setenv("SPECWORKS_RUN_CACHE", "0")
    gate_tests()
    gate_tests()
    assert runs(counter) == 2


def test_specworks_run_always_runs(counted):
    repo, counter = counted
    gate_tests()
    for _ in range(2):
        run_json("run", "test", "--change", REF)
    assert runs(counter) == 3


def test_without_git_every_run_is_real(project, tmp_path_factory):
    counter = tmp_path_factory.mktemp("runs") / "count"
    counter.write_text("")
    command = f'"{sys.executable}" -c "open(r\'{counter}\', \'a\').write(\'x\')"'
    cfg = project / "spec.yml"
    cfg.write_text(re.sub(r"(?m)^  test:.*$", lambda _: f"  test: {json.dumps(command)}", cfg.read_text(), count=1))
    gate_tests()
    gate_tests()
    assert runs(counter) == 2


def test_edits_inside_a_git_submodule_rerun(counted, tmp_path_factory):
    repo, counter = counted
    lib = tmp_path_factory.mktemp("lib")
    git(lib, "init", "-q", "-b", "main")
    (lib / "lib.py").write_text("x = 1\n")
    git(lib, "add", "-A")
    git(lib, "commit", "-q", "-m", "lib")
    git(repo, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(lib), "vendor/lib")
    git(repo, "commit", "-q", "-m", "add lib")
    gate_tests()
    (repo / "vendor/lib/lib.py").write_text("x = 2\n")  # the submodule is now dirty
    gate_tests()
    (repo / "vendor/lib/lib.py").write_text("x = 3\n")  # still dirty, but other content
    gate_tests()
    assert runs(counter) == 3
    (repo / "vendor/lib/new.py").write_text("a = 1\n")  # untracked inside the submodule: git shows no content, so never reuse
    gate_tests()
    gate_tests()
    assert runs(counter) == 5
