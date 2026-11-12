"""
Code phase support: `specworks run` and the code gate.
"""

import pytest

from helpers import REF, run_json


def test_tag_scan_skips_files_too_large_or_not_text(project):
    (project / "src/auth/lockout.py").write_text("# @req REQ-AUTH-002\nLIMIT = 3\n")  # specworks: ignore-tags
    (project / "src/auth/big.py").write_text("# @req REQ-AUTH-003\n" + "x = 1\n" * 200_000)  # over 1 MB: not read  # specworks: ignore-tags
    (project / "src/auth/legacy.py").write_bytes("# @req REQ-AUTH-003 café\n".encode("latin-1"))  # not UTF-8: not read  # specworks: ignore-tags
    code, data = run_json("trace", "--change", REF)
    assert data["gaps"]["reqWithoutCode"] == ["REQ-AUTH-003"]


def test_tag_scan_follows_a_symlink_to_a_file_outside_the_workspace(project, tmp_path_factory):
    shared = tmp_path_factory.mktemp("shared") / "reset.py"
    shared.write_text("# @req REQ-AUTH-003\n")  # specworks: ignore-tags
    try:
        (project / "src/auth/reset.py").symlink_to(shared)
    except OSError:  # Windows without the symlink privilege
        pytest.skip("cannot create symlinks here")
    code, data = run_json("trace", "--change", REF)
    assert "REQ-AUTH-003" not in data["gaps"]["reqWithoutCode"]
    assert any("src/auth/reset.py:1" in code_at for row in data["rows"] for code_at in row["code"])
