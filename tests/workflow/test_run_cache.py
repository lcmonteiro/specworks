"""Gates reuse the result of a project command run on an identical working tree."""

import pytest

from helpers import REF, run_json
from support.run_cache import gate_tests, make_counted, runs


@pytest.fixture
def counted(repo, tmp_path_factory):
    return make_counted(repo, tmp_path_factory)


# @ac AC-FLOW-003.3
@pytest.mark.parametrize("command", [["gate", "review"], ["validate", "--base", "main"]])
def test_fresh_runs_the_commands_again(counted, command):
    repo, counter = counted
    gate_tests()
    code, data = run_json(*command, "--change", REF, "--fresh")
    assert runs(counter) == 2
    assert not any("same code as the run at" in d for c in data["checks"] for d in c["details"])


# @ac AC-FLOW-003.3
def test_fresh_runs_each_command_once_for_all_the_gates_of_a_start(counted):
    repo, counter = counted
    gate_tests()
    (repo / ".specworks/changes/active" / REF / "design.md").write_text("# Design\n\n## Interfaces\n\nNone\n")
    run_json("phase", "design", "--change", REF)
    code, data = run_json("start", "review", "--change", REF, "--fresh")  # gates design, test and code
    assert code == 0, data
    assert runs(counter) == 2
