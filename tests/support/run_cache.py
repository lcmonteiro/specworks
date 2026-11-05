"""Helpers shared by the run_cache tests of several capabilities."""

import json
import re
import sys

from helpers import REF, run_json

TESTS = "the test suite passes (commands.test)"


def make_counted(repo, tmp_path_factory, key="test"):
    """The repo with a ``commands.<key>`` command that counts its runs in a file outside the repo (so counting changes nothing)."""
    counter = tmp_path_factory.mktemp("runs") / "count"
    counter.write_text("")
    command = f'"{sys.executable}" -c "open(r\'{counter}\', \'a\').write(\'x\')"'
    cfg = repo / ".specworks/config.yml"
    cfg.write_text(re.sub(rf"(?m)^  {key}:.*$", lambda _: f"  {key}: {json.dumps(command)}", cfg.read_text(), count=1))
    return repo, counter


def gate_tests():
    code, data = run_json("gate", "review", "--change", REF)  # the code gate does not run the tests
    return next(c for c in data["checks"] if c["name"] == TESTS)


def runs(counter):
    return len(counter.read_text())
