"""Staying in the workspace: file tools rooted in it, a shell that runs there and refuses `git push` (REQ-HARNESS-008)."""

import pytest

from specworks.harness.confine import confined, refuses
from specworks.harness.workspaces import Workspaces

TEST = 1


@pytest.fixture
def layout(tmp_path):
    """A workspace folder, and a file next to it, outside."""
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "inside.txt").write_text("inside\n", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    return root, outside


def content(result):
    data = result.file_data or {}
    return str(data.get("content", ""))


# @ac AC-HARNESS-008.1
@pytest.mark.parametrize("how", ["relative", "absolute"])
def test_ac_harness_008_1_reading_outside(layout, how):
    root, outside = layout
    path = "../outside.txt" if how == "relative" else str(outside)
    result = confined(root).read(path)
    assert result.error
    assert "secret" not in content(result)


# @ac AC-HARNESS-008.1
@pytest.mark.parametrize("how", ["relative", "absolute"])
def test_ac_harness_008_1_writing_outside(layout, how):
    root, outside = layout
    target = outside.parent / "written.txt"
    path = "../written.txt" if how == "relative" else str(target)
    result = confined(root).write(path, "x")
    assert result.error
    assert not target.exists()
    assert outside.read_text(encoding="utf-8") == "secret\n"
    overwrite = confined(root).write("../outside.txt" if how == "relative" else str(outside), "x")
    assert overwrite.error
    assert outside.read_text(encoding="utf-8") == "secret\n"


# @ac AC-HARNESS-008.1
def test_ac_harness_008_1_inside_still_works(layout):
    root, _ = layout
    backend = confined(root)
    assert "inside" in content(backend.read("/inside.txt"))
    assert backend.write("/new.txt", "new\n").error is None
    assert (root / "new.txt").read_text(encoding="utf-8") == "new\n"


# @ac AC-HARNESS-008.2
def test_ac_harness_008_2_the_shells_folder(project, ws, module):
    spaces = Workspaces(ws, module)
    path = spaces.open("test-half", TEST)
    response = confined(spaces.path_of(TEST)).execute("pwd")
    assert response.exit_code == 0
    assert response.output.strip().splitlines()[-1] == str(path.resolve())


# @ac AC-HARNESS-008.3
@pytest.mark.parametrize("command", ["git push", "git push origin main", "touch ran && git push origin main", "touch ran && git -C . push origin main"])
def test_ac_harness_008_3_no_push(tmp_path, command):
    assert refuses(command)
    response = confined(tmp_path).execute(command)
    assert response.exit_code != 0
    assert not (tmp_path / "ran").exists()


# @ac AC-HARNESS-008.3
@pytest.mark.parametrize("command", ["git status", "echo pushed", "git stash push -m wip", 'git commit -m "push later"'])
def test_ac_harness_008_3_other_commands_run(tmp_path, command):
    assert not refuses(command)
    response = confined(tmp_path).execute(command)
    assert "refused" not in response.output
