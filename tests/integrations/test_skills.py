import shutil

import pytest

from helpers import set_saved_tools
from specworks.cli import app
from specworks.core.config import load_config
from specworks.tools import skills as skills_module
from specworks.tools.skills import TOOLS, ToolError, fill_includes, packaged_skills, read_skill, render_skill, resolve_tools, skill_folders
from support.skills import MULTILINE, SKILL, fake_shared, frontmatter, init, installed_files, runner, specworks_skills_in, state_of


# @ac AC-INTEG-004.1
def test_no_tool_detected_installs_for_all(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch)
    assert (tmp_path / f".claude/skills/{SKILL}/SKILL.md").is_file()  # Copilot reads .claude/skills/ too
    assert specworks_skills_in(tmp_path / ".github/skills") == [] and not (tmp_path / ".github/prompts").exists()
    assert load_config(tmp_path).tools == ["claude", "copilot"]


# @ac AC-INTEG-005.2
def test_copilot_only(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "copilot")
    assert not (tmp_path / ".claude").exists()
    skill = tmp_path / f".github/skills/{SKILL}/SKILL.md"
    meta = frontmatter(skill)
    assert f"name: {SKILL}\n" in meta and "description:" in meta
    assert "allowed-tools" not in meta  # Claude Code tool names mean nothing to Copilot
    assert "## Steps" in skill.read_text()
    assert not (tmp_path / ".github/prompts").exists()


# @ac AC-INTEG-005.2
def test_claude_copy_keeps_allowed_tools(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    assert "allowed-tools:" in frontmatter(tmp_path / f".claude/skills/{SKILL}/SKILL.md")
    assert not (tmp_path / ".github").exists()


# @ac AC-INTEG-004.2
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


# @ac AC-INTEG-004.4
def test_an_empty_tool_list_is_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--tools", ","])
    assert result.exit_code == 1 and "no tool given" in result.output
    assert list(tmp_path.iterdir()) == []

# @ac AC-INTEG-005.1
@pytest.mark.parametrize("tool, folder", [("copilot", ".github/skills"), ("claude", ".claude/skills")])
def test_every_packaged_skill_is_installed(tmp_path, monkeypatch, tool, folder):
    init(tmp_path, monkeypatch, "--tools", tool)
    for name in packaged_skills():
        assert name.startswith("specworks-") and (tmp_path / f"{folder}/{name}/SKILL.md").is_file()
    assert specworks_skills_in(tmp_path / folder) == packaged_skills()
    assert not (tmp_path / ".github/prompts").exists()  # skills are the slash commands: no prompt file


# @ac AC-INTEG-004.3
def test_unknown_tool_is_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--tools", "cursor"])
    assert result.exit_code == 1 and "unknown tool 'cursor'" in result.output
    assert list(tmp_path.iterdir()) == []


# @ac AC-INTEG-005.5
def test_skills_command_refreshes(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    result = runner.invoke(app, ["skills", "--tools", "copilot"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / f".github/skills/{SKILL}/SKILL.md").is_file()


# @ac AC-INTEG-005.5
def test_module_init_installs_skills_at_workspace_root(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "copilot")
    runner.invoke(app, ["init", "services/billing", "--tools", "copilot"])
    assert not (tmp_path / "services/billing/.github").exists()


# @ac AC-INTEG-005.4
@pytest.mark.parametrize("tool, folder", [("claude", ".claude/skills"), ("copilot", ".github/skills")])
def test_installed_skills_have_their_shared_parts_filled_in(tmp_path, monkeypatch, tool, folder):
    init(tmp_path, monkeypatch, "--tools", tool)
    for name in packaged_skills():
        path = tmp_path / f"{folder}/{name}/SKILL.md"
        text = path.read_text()
        assert "specworks:include" not in text and "**Running the CLI**" in text, path


# @ac AC-INTEG-005.8
def test_claude_code_and_copilot_share_the_claude_folder(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude,copilot")
    assert specworks_skills_in(tmp_path / ".claude/skills") == packaged_skills()
    assert "allowed-tools:" in frontmatter(tmp_path / f".claude/skills/{SKILL}/SKILL.md")  # the folder is Claude Code's: its keys
    assert specworks_skills_in(tmp_path / ".github/skills") == [] and not (tmp_path / ".github/prompts").exists()


# @ac AC-INTEG-005.8
@pytest.mark.parametrize(
    "chosen, folders",
    [
        (["claude", "copilot"], [("claude", ".claude/skills")]),
        (["copilot", "claude"], [("claude", ".claude/skills")]),  # taken in TOOLS order, whatever the order given
        (["copilot"], [("copilot", ".github/skills")]),
        (["claude"], [("claude", ".claude/skills")]),
    ],
)
def test_skill_folders_are_the_fewest_every_tool_reads(chosen, folders):
    assert [(tool.id, folder) for tool, folder in skill_folders([TOOLS[t] for t in chosen])] == folders


# @ac AC-INTEG-005.9
def test_copies_an_older_version_left_for_copilot_are_removed(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    old = {
        f".github/skills/{SKILL}/SKILL.md": "old\n",
        f".github/prompts/{SKILL}.prompt.md": "old\n",
        ".github/skills/my-skill/SKILL.md": "mine\n",
        ".github/prompts/my.prompt.md": "mine\n",
    }
    for rel, text in old.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    result = runner.invoke(app, ["skills", "--tools", "claude,copilot"])
    assert result.exit_code == 0, result.output
    for rel in (f".github/skills/{SKILL}", f".github/prompts/{SKILL}.prompt.md"):
        assert not (tmp_path / rel).exists() and f"removed {rel}" in result.output, rel
    assert (tmp_path / ".github/skills/my-skill/SKILL.md").is_file() and (tmp_path / ".github/prompts/my.prompt.md").is_file()
    assert "my-skill" not in result.output and "my.prompt.md" not in result.output
    assert (tmp_path / f".claude/skills/{SKILL}/SKILL.md").is_file()


# @ac AC-INTEG-004.5
def test_the_saved_tools_are_used_without_tools(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--no-skills")
    set_saved_tools(tmp_path, "[copilot]")
    (tmp_path / "CLAUDE.md").write_text("# Claude\n")  # auto would pick Claude Code
    result = runner.invoke(app, ["skills"])
    assert result.exit_code == 0, result.output
    assert specworks_skills_in(tmp_path / ".github/skills") == packaged_skills()
    assert not (tmp_path / ".claude").exists()
    assert load_config(tmp_path).tools == ["copilot"]


# @ac AC-INTEG-004.6
def test_tools_given_replace_the_saved_tools(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--no-skills")
    set_saved_tools(tmp_path, "[claude]")
    result = runner.invoke(app, ["skills", "--tools", "claude,copilot"])
    assert result.exit_code == 0, result.output
    text = (tmp_path / ".specworks/config.yml").read_text(encoding="utf-8")
    assert "tools: [claude, copilot]" in text and load_config(tmp_path).tools == ["claude", "copilot"]
    assert specworks_skills_in(tmp_path / ".claude/skills") == packaged_skills()  # one folder both tools read
    assert state_of(tmp_path) == ("current", set())


# @ac AC-INTEG-004.7
def test_the_installed_tools_are_saved_when_none_is_saved(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    set_saved_tools(tmp_path, None)  # a project from before tools were saved
    result = runner.invoke(app, ["skills"])
    assert result.exit_code == 0, result.output
    assert load_config(tmp_path).tools == ["claude"]  # inferred from the folders, not auto (which would be both here)
    assert "tools: [claude]" in (tmp_path / ".specworks/config.yml").read_text(encoding="utf-8")
    assert specworks_skills_in(tmp_path / ".claude/skills") == packaged_skills() and not (tmp_path / ".github").exists()


# @ac AC-INTEG-004.5, AC-INTEG-004.6, AC-INTEG-004.7
def test_resolve_tools_prefers_given_then_saved_then_installed(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github/copilot-instructions.md").write_text("# Copilot\n")  # auto would add Copilot

    def ids(resolved):
        return [t.id for t in resolved[0]], resolved[1]

    assert ids(resolve_tools(tmp_path, ["claude"], "claude,copilot")) == (["claude", "copilot"], True)
    assert ids(resolve_tools(tmp_path, ["copilot"], None)) == (["copilot"], False)
    assert ids(resolve_tools(tmp_path, None, None)) == (["claude"], True)


# @ac AC-INTEG-005.6
def test_skills_that_are_no_longer_shipped_are_removed(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "all")
    stale = []
    for name in ("specworks-propose", "sw-refine", "my-skill"):
        for folder in (".claude/skills", ".github/skills"):
            (tmp_path / folder / name).mkdir(parents=True)
            (tmp_path / folder / name / "SKILL.md").write_text("old\n")
            stale.append(f"{folder}/{name}")
        (tmp_path / ".github/prompts").mkdir(parents=True, exist_ok=True)
        (tmp_path / f".github/prompts/{name}.prompt.md").write_text("old\n")
        stale.append(f".github/prompts/{name}.prompt.md")
    result = runner.invoke(app, ["skills", "--tools", "all"])
    assert result.exit_code == 0, result.output
    for path in stale:
        if "my-skill" in path:
            assert (tmp_path / path).exists(), path  # not specworks': never touched
        else:
            assert not (tmp_path / path).exists() and f"removed {path}" in result.output, path
    assert all((tmp_path / f".claude/skills/{name}/SKILL.md").is_file() for name in packaged_skills())


# @ac AC-INTEG-005.6
def test_a_stale_skill_that_is_a_symlink_is_unlinked_not_followed(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    target = tmp_path / "elsewhere/specworks-verify"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("old\n")
    try:
        (tmp_path / ".claude/skills/specworks-verify").symlink_to(target, target_is_directory=True)
    except OSError:  # Windows without the symlink privilege
        pytest.skip("cannot create symlinks here")
    result = runner.invoke(app, ["skills", "--tools", "claude"])
    assert result.exit_code == 0, result.output
    assert "removed .claude/skills/specworks-verify" in result.output
    assert not (tmp_path / ".claude/skills/specworks-verify").exists() and (target / "SKILL.md").is_file()


# @ac AC-INTEG-005.7
def test_a_multi_line_frontmatter_value_is_kept_or_dropped_whole():
    description = "description: >\n  Does x.\n  Use when: the user asks for x.\n"
    github, claude = render_skill(MULTILINE, TOOLS["copilot"]), render_skill(MULTILINE, TOOLS["claude"])  # the .github/skills/ and .claude/skills/ copies
    assert github == "---\nname: specworks-x\n" + description + "---\n# Body\n"  # allowed-tools dropped with its second line
    assert claude == MULTILINE


# @ac AC-INTEG-005.7
@pytest.mark.parametrize("name", packaged_skills())
def test_one_line_frontmatter_is_copied_as_before(name):
    text = read_skill(name)
    head, body = text.split("---\n", 2)[1], text.split("---\n", 2)[2]
    lines = [line for line in head.splitlines() if ":" in line]  # every packaged skill: one line per key
    assert all(not line.startswith((" ", "\t")) for line in head.splitlines())
    copilot = [line for line in lines if line.split(":", 1)[0] in ("name", "description")]
    assert render_skill(text, TOOLS["copilot"]) == "---\n" + "\n".join(copilot) + "\n---\n" + body
    assert render_skill(text, TOOLS["claude"]) == "---\n" + "\n".join(lines) + "\n---\n" + body


# @ac AC-INTEG-006.1
def test_skills_just_installed_are_current(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "all")
    assert state_of(tmp_path) == ("current", set())


# @ac AC-INTEG-006.2
def test_an_edited_skill_is_outdated(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "all")
    (tmp_path / f".claude/skills/{SKILL}/SKILL.md").write_text("edited\n", encoding="utf-8")
    assert state_of(tmp_path) == ("outdated", {(f".claude/skills/{SKILL}/SKILL.md", "changed")})


# @ac AC-INTEG-006.3
def test_a_deleted_skill_is_missing(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "copilot")
    shutil.rmtree(tmp_path / f".github/skills/{SKILL}")
    assert state_of(tmp_path) == ("outdated", {(f".github/skills/{SKILL}/SKILL.md", "missing")})


# @ac AC-INTEG-006.4
def test_a_skill_no_longer_shipped_is_stale_and_a_users_own_is_ignored(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    for name in ("specworks-propose", "my-skill"):
        (tmp_path / f".claude/skills/{name}").mkdir()
        (tmp_path / f".claude/skills/{name}/SKILL.md").write_text("old\n")
    assert state_of(tmp_path) == ("outdated", {(".claude/skills/specworks-propose", "stale")})


# @ac AC-INTEG-006.6
def test_copies_an_older_version_left_are_stale(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    set_saved_tools(tmp_path, "[claude, copilot]")
    (tmp_path / f".github/skills/{SKILL}").mkdir(parents=True)
    (tmp_path / f".github/skills/{SKILL}/SKILL.md").write_text("old\n", encoding="utf-8")
    (tmp_path / ".github/prompts").mkdir()
    (tmp_path / f".github/prompts/{SKILL}.prompt.md").write_text("old\n", encoding="utf-8")
    assert state_of(tmp_path) == ("outdated", {(f".github/skills/{SKILL}", "stale"), (f".github/prompts/{SKILL}.prompt.md", "stale")})


# @ac AC-INTEG-006.5
def test_no_skills_installed(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--no-skills")
    assert state_of(tmp_path) == ("none", set())


# @ac AC-INTEG-007.1
def test_ac_integ_007_1_a_parameter_is_filled_in():
    text = "# Skill\n<!-- specworks:include record phase=test -->\nAfter.\n"
    filled = fill_includes(text, "specworks-x", fake_shared({"record": "Record it with --in {{phase}}.\n"}))
    assert filled == "# Skill\nRecord it with --in test.\nAfter.\n"


# @ac AC-INTEG-007.2
def test_ac_integ_007_2_a_quoted_value_is_filled_in():
    text = '<!-- specworks:include who who="the code half" -->\n'
    filled = fill_includes(text, "specworks-x", fake_shared({"who": "Done by {{who}}.\n"}))
    assert filled == "Done by the code half.\n"


# @ac AC-INTEG-007.3
def test_ac_integ_007_3_a_placeholder_left_unfilled_fails():
    text = "<!-- specworks:include record -->\n"
    with pytest.raises(ToolError) as error:
        fill_includes(text, "specworks-x", fake_shared({"record": "Record it with --in {{phase}}.\n"}))
    message = str(error.value)
    assert "leaves {{phase}} unfilled" in message and "specworks-x" in message and "record" in message


# @ac AC-INTEG-007.4
def test_ac_integ_007_4_a_key_the_shared_file_does_not_use_fails():
    text = "<!-- specworks:include record colour=red -->\n"
    with pytest.raises(ToolError) as error:
        fill_includes(text, "specworks-x", fake_shared({"record": "No placeholder here.\n"}))
    message = str(error.value)
    assert "does not use colour" in message and "specworks-x" in message and "record" in message


# @ac AC-INTEG-007.5
def test_ac_integ_007_5_an_include_without_parameters_is_copied_exactly():
    shared = "Use `a\\1` and {single} braces, $HOME and — as they are.\n\nSecond paragraph.\n"
    filled = fill_includes("Before.\n<!-- specworks:include plain -->\nAfter.\n", "specworks-x", fake_shared({"plain": shared}))
    assert filled == f"Before.\n{shared}After.\n"


# @ac AC-INTEG-007.6
def test_ac_integ_007_6_nothing_is_written_when_a_packaged_include_fails(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    stale = tmp_path / ".claude/skills/specworks-retired/SKILL.md"  # a specworks skill this version does not ship
    stale.parent.mkdir(parents=True)
    stale.write_text("old\n", encoding="utf-8")
    (tmp_path / f".claude/skills/{SKILL}/SKILL.md").write_text("old\n", encoding="utf-8")
    before = installed_files(tmp_path)
    real = skills_module.fill_includes

    def failing(text, skill, shared):
        if skill == "specworks-test":
            raise ToolError(f"skill {skill}: include back-from-review leaves {{{{phase}}}} unfilled")
        return real(text, skill, shared)

    monkeypatch.setattr(skills_module, "fill_includes", failing)
    result = runner.invoke(app, ["skills", "--tools", "claude"])
    assert result.exit_code == 1, result.output
    assert "leaves {{phase}} unfilled" in result.output
    assert installed_files(tmp_path) == before


# @ac AC-INTEG-007.8
def test_ac_integ_007_8_update_changes_nothing_when_a_packaged_include_fails(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    stale = tmp_path / ".claude/skills/specworks-retired"  # a specworks skill this version does not ship: update would remove it
    stale.mkdir()
    (stale / "SKILL.md").write_text("old\n", encoding="utf-8")
    (tmp_path / f".claude/skills/{SKILL}/SKILL.md").write_text("old\n", encoding="utf-8")  # outdated: update would rewrite it
    before = installed_files(tmp_path)
    real = skills_module.fill_includes

    def failing(text, skill, shared):
        if skill == "specworks-test":
            raise ToolError(f"skill {skill}: include back-from-review leaves {{{{phase}}}} unfilled")
        return real(text, skill, shared)

    monkeypatch.setattr(skills_module, "fill_includes", failing)
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 1, result.output
    assert "leaves {{phase}} unfilled" in result.output
    assert (stale / "SKILL.md").read_text(encoding="utf-8") == "old\n"
    assert installed_files(tmp_path) == before


# @ac AC-INTEG-007.7
@pytest.mark.parametrize("name", packaged_skills())
def test_ac_integ_007_7_every_packaged_skill_fills_in(name):
    text = read_skill(name)
    assert "{{" not in text and "specworks:include" not in text
