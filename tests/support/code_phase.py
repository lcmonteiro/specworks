"""
Helpers shared by the code_phase tests of several capabilities.
"""

import json
import re
import sys

PASS = f'"{sys.executable}" -c "print(\'all green\')"'
FAIL = f'"{sys.executable}" -c "import sys; print(\'2 failed\'); sys.exit(3)"'


def set_test_command(root, command):
    cfg = root / ".specworks/config.yml"
    text = cfg.read_text()
    cfg.write_text(re.sub(r"(?m)^  test:.*$", lambda _: f"  test: {json.dumps(command)}", text, count=1))
