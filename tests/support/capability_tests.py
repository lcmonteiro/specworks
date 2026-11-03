"""Helpers shared by the capability_tests tests of several capabilities."""

import json
import sys
from pathlib import Path

from helpers import init_repo, runner
from specworks.cli import app

# A test command that records each run (its mode, its arguments and its folder) in a log outside the repo, and fails
# when a Python file under the folders it is given (the current folder for the full suite) holds `assert False`.
RECORDER = """\
import json, os, sys
log, mode, *paths = sys.argv[1:]
with open(log, "a", encoding="utf-8") as f:
    f.write(json.dumps({"mode": mode, "paths": paths, "cwd": os.getcwd()}) + "\\n")
failing = []
for top in paths or ["."]:
    for folder, _, names in os.walk(top):
        for name in names:
            if name.endswith(".py"):
                with open(os.path.join(folder, name), encoding="utf-8") as source:
                    if "assert False" in source.read():
                        failing.append(os.path.join(folder, name))
print(mode, len(paths), "failed" if failing else "passed")
sys.exit(1 if failing else 0)
"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def recorder_command(recorder, log, mode, placeholder=""):
    return json.dumps(f'"{sys.executable}" "{recorder}" "{log}" {mode}{placeholder}')


def make_log(tmp_path_factory):
    """The run log of the recorder test commands, outside every sample project, and the recorder itself."""
    folder = tmp_path_factory.mktemp("runs")
    recorder = folder / "recorder.py"
    recorder.write_text(RECORDER, encoding="utf-8")
    run_log = folder / "runs.jsonl"
    run_log.write_text("", encoding="utf-8")
    return recorder, run_log


def commands_block(log, scoped=True):
    recorder, run_log = log
    lines = f"commands:\n  test: {recorder_command(recorder, run_log, 'full')}\n"
    if scoped:
        lines += f"  test_scoped: {recorder_command(recorder, run_log, 'scoped', ' {paths}')}\n"
    return lines


def runs(log, root):
    """Each recorded run as (mode, folders, folder it ran in relative to ``root``)."""
    _, run_log = log
    entries = [json.loads(line) for line in run_log.read_text(encoding="utf-8").splitlines() if line]
    return [(e["mode"], e["paths"], Path(e["cwd"]).resolve().relative_to(root.resolve()).as_posix()) for e in entries]


def new_project(root, monkeypatch, config_tail="", capabilities="", commands="commands:\n  test:\n  lint:\n"):
    monkeypatch.chdir(root)
    init_repo(root)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    cfg = root / ".specworks/config.yml"
    text = cfg.read_text(encoding="utf-8")
    text = text.replace("capabilities: {}", f"capabilities:\n{capabilities}" if capabilities else "capabilities: {}")
    text = text.replace("commands:\n  test:\n  lint:\n", commands)
    cfg.write_text(text + config_tail, encoding="utf-8")
    return root


def add_billing_module(root, billing_config=""):
    """Module billing at services/billing with capability invoices (src/invoices) and ``billing_config`` appended."""
    assert runner.invoke(app, ["module", "add", "services/billing"]).exit_code == 0
    cfg = root / "services/billing/.specworks/config.yml"
    text = cfg.read_text(encoding="utf-8").replace("capabilities: {}", "capabilities:\n  invoices:\n    path: src/invoices")
    cfg.write_text(text + billing_config, encoding="utf-8")
    return root / "services/billing"
