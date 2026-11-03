"""Gates reuse the result of a project command run on an identical working tree."""

import pytest

from helpers import REF, run_json
from support.run_cache import gate_tests, make_counted, runs


@pytest.fixture
def counted(repo, tmp_path_factory):
    return make_counted(repo, tmp_path_factory)


def test_close_runs_the_commands_but_its_dry_run_reuses(counted):
    repo, counter = counted
    (repo / ".specworks/changes/active" / REF / "review.md").write_text("# Review\n\n## Findings\n\nNone.\n")
    run_json("phase", "review", "--change", REF)
    gate_tests()
    code, data = run_json("close", "--change", REF, "--base", "main", "--dry-run")
    assert code == 0, data
    assert runs(counter) == 1
    code, data = run_json("close", "--change", REF, "--base", "main")
    assert code == 0, data
    assert runs(counter) == 2
