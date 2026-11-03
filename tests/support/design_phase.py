"""Helpers shared by the design_phase tests of several capabilities."""

import json
import re
import sys

PASS = f'"{sys.executable}" -c "print(\'all green\')"'


def set_commands(root, **commands):
    cfg = root / ".specworks/config.yml"
    text = cfg.read_text()
    block = "".join(f"  {key}: {json.dumps(value)}\n" for key, value in commands.items())
    cfg.write_text(re.sub(r"(?m)^commands:\n(  .*\n)*", lambda _: "commands:\n" + block, text, count=1))


def make_planned(project):
    set_commands(project, test=PASS)
    return project
