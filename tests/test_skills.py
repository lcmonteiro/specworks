import re

import pytest
from typer.testing import CliRunner

from specworks.cli import app
from specworks.tools.skills import packaged_skills, read_skill

runner = CliRunner()
SKILL = "specworks-refine"


def init(tmp_path, monkeypatch, *args):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", *args])
    assert result.exit_code == 0, result.output
    return result.output


def frontmatter(path):
    return path.read_text().split("---\n")[1]


def test_no_tool_detected_installs_for_all(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch)
    assert (tmp_path / f".claude/skills/{SKILL}/SKILL.md").is_file()
    assert (tmp_path / f".github/skills/{SKILL}/SKILL.md").is_file()
    assert (tmp_path / f".github/prompts/{SKILL}.prompt.md").is_file()


def test_copilot_only(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "copilot")
    assert not (tmp_path / ".claude").exists()
    skill = tmp_path / f".github/skills/{SKILL}/SKILL.md"
    meta = frontmatter(skill)
    assert f"name: {SKILL}\n" in meta and "description:" in meta
    assert "allowed-tools" not in meta  # Claude Code tool names mean nothing to Copilot
    assert "## Steps" in skill.read_text()


def test_copilot_prompt_file_is_an_agent_mode_slash_command(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "copilot")
    prompt = tmp_path / f".github/prompts/{SKILL}.prompt.md"
    meta = frontmatter(prompt)
    assert meta.startswith("description: ") and "agent: agent" in meta
    assert "name:" not in meta  # the file name is the command name
    assert "specworks context --json" in prompt.read_text()


def test_claude_copy_keeps_allowed_tools(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    assert "allowed-tools:" in frontmatter(tmp_path / f".claude/skills/{SKILL}/SKILL.md")
    assert not (tmp_path / ".github").exists()


@pytest.mark.parametrize(
    "marker, expected",
    [(".github/copilot-instructions.md", {".github"}), ("CLAUDE.md", {".claude"})],
)
def test_auto_detects_tool_in_use(tmp_path, monkeypatch, marker, expected):
    (tmp_path / marker).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / marker).write_text("x")
    init(tmp_path, monkeypatch, "--no-link")
    installed = {d for d in (".claude", ".github") if (tmp_path / d / "skills").is_dir()}
    assert installed == expected


def test_every_packaged_skill_is_installed(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "all")
    for name in packaged_skills():
        assert (tmp_path / f".claude/skills/{name}/SKILL.md").is_file()
        assert (tmp_path / f".github/skills/{name}/SKILL.md").is_file()
        assert (tmp_path / f".github/prompts/{name}.prompt.md").is_file()


def test_unknown_tool_is_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--tools", "cursor"])
    assert result.exit_code == 1 and "unknown tool 'cursor'" in result.output
    assert list(tmp_path.iterdir()) == []


def test_skills_command_refreshes(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    result = runner.invoke(app, ["skills", "--tools", "copilot"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / f".github/skills/{SKILL}/SKILL.md").is_file()


def test_module_init_installs_skills_at_workspace_root(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "copilot")
    runner.invoke(app, ["init", "services/billing", "--tools", "copilot"])
    assert not (tmp_path / "services/billing/.github").exists()


def test_skills_renamed_in_the_phase_rename_are_removed(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "all")
    old = [tmp_path / ".claude/skills/specworks-propose/SKILL.md", tmp_path / ".github/skills/specworks-verify/SKILL.md"]
    prompt = tmp_path / ".github/prompts/specworks-implement.prompt.md"
    kept = tmp_path / ".claude/skills/specworks-interface/notes.md"  # not ours: the folder stays
    for path in [*old, prompt, kept]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("old")
    result = runner.invoke(app, ["skills", "--tools", "all"])
    assert result.exit_code == 0, result.output
    assert "removed .claude/skills/specworks-propose/SKILL.md (renamed skill)" in result.output
    assert not any(p.exists() for p in old) and not prompt.exists()
    assert not (tmp_path / ".claude/skills/specworks-propose").exists() and kept.is_file()
    assert (tmp_path / ".claude/skills/specworks-specify/SKILL.md").is_file()


def test_installed_skills_have_their_shared_parts_filled_in(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "all")
    for name in packaged_skills():
        for path in (tmp_path / f".claude/skills/{name}/SKILL.md", tmp_path / f".github/prompts/{name}.prompt.md"):
            text = path.read_text()
            assert "specworks:include" not in text and "**Running the CLI**" in text, path


def test_skill_triggers_name_specworks(tmp_path, monkeypatch):
    # Descriptions decide when an agent loads a skill: each one is scoped to specworks, not to any "test" or "review".
    init(tmp_path, monkeypatch, "--tools", "claude")
    for name in packaged_skills():
        description = next(line for line in frontmatter(tmp_path / f".claude/skills/{name}/SKILL.md").splitlines() if line.startswith("description:"))
        use_when = description.split("Use ", 1)[1]
        assert "specworks" in use_when and f'"{name.replace("-", " ")}"' in use_when, name


def test_validate_enters_its_phase_through_the_review_gate():
    # `specworks phase` would move the change unchecked and make "the change went through review" always pass.
    text = read_skill("specworks-validate")
    assert 'specworks start validate --change "<ref>"' in text
    assert 'specworks phase "<ref>" validate' not in text


def test_specify_marks_the_review_findings_it_carried_out():
    # Without the mark, `specworks cycle` keeps handing a spec finding back to specify and the build never resumes.
    assert "done in specify:" in read_skill("specworks-specify")
    assert "done in specify:" in read_skill("specworks-build")


UVX = "uvx --from git+https://github.com/lcmonteiro/specworks specworks"


@pytest.mark.parametrize("name", packaged_skills())
def test_skills_pre_approve_only_specworks_and_read_only_git(name):
    # A bare `Bash(uvx:*)` would let the skill run any package without asking.
    allowed = re.search(r"^allowed-tools: (.*)$", read_skill(name), re.MULTILINE).group(1)
    commands = re.findall(r"Bash\(([^)]*):\*\)", allowed)
    assert set(commands) <= {"specworks", "uv run specworks", UVX, "git diff", "git log", "git status"}, commands
    assert UVX in commands and f"`{UVX} <cmd>`" in read_skill(name)  # the rule matches the command the skill documents


@pytest.mark.parametrize("name", [n for n in packaged_skills() if n != "specworks-refine"])
def test_skills_pick_the_change_by_one_shared_rule(name):
    # "Select the change as the other phases do" pointed at no rule; the shared paragraph is that rule.
    text = read_skill(name)
    assert "**Picking the change**" in text and "Pick the change (above)" in text
    assert "as the other phases do" not in text and "as in `/specworks-specify`" not in text
