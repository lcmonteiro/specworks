"""Helpers shared by the diagrams tests of several capabilities."""

import json

from typer.testing import CliRunner

from helpers import fake_executable, init_repo
from specworks.cli import app

runner = CliRunner()
CHANGE = "add-reset"
FLOW = 'shape: sequence_diagram\nuser: User\napi: Auth API\nuser -> api: "POST /reset {email}"\n'


def run_json(*args):
    result = runner.invoke(app, [*args, "--json"])
    return result.exit_code, json.loads(result.output)


def make_fake_d2(tmp_path_factory, monkeypatch):
    """A stand-in for d2 that records its arguments and writes a small SVG."""
    folder = tmp_path_factory.mktemp("bin")
    script = fake_executable(
        folder,
        "d2",
        "import sys, pathlib\n"
        "src, out = sys.argv[-2], sys.argv[-1]\n"
        "if 'BROKEN' in pathlib.Path(src).read_text():\n"
        "    print('err: failed to compile: unexpected token', file=sys.stderr); sys.exit(1)\n"
        "pathlib.Path(out).write_text('<?xml version=\"1.0\"?><svg viewBox=\"0 0 1 1\">' + ' '.join(sys.argv[1:-2]) + '</svg>')\n",
    )
    monkeypatch.setenv("SPECWORKS_D2", str(script))
    return script


def make_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    assert runner.invoke(app, ["init", "--no-skills"]).exit_code == 0
    run_json("new", CHANGE, "--no-branch")
    path = tmp_path / ".specworks/changes/active" / CHANGE
    (path / "diagrams").mkdir()
    (path / "diagrams/reset-flow.d2").write_text(FLOW)
    (path / "design.md").write_text("# Design\n\n![Reset flow (REQ-AUTH-003)](diagrams/reset-flow.svg)\n")
    return path


def set_diagrams(change, block):
    cfg = change.parents[3] / ".specworks/config.yml"
    text = cfg.read_text()
    cfg.write_text(text[: text.index("\ndiagrams:\n") + 1] + block)
