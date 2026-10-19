import re
import shlex
from importlib import resources

import pytest
import typer.main
from typer.testing import CliRunner

from specworks.cli import app
from specworks.core.changes import PHASES
from specworks.core.config import COMMAND_KEYS
from specworks.tools.skills import packaged_skills, read_skill
from specworks.workflow.artifacts import load_artifacts
from specworks.workflow.gate import GATES

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


# refine, adopt and baseline create the change they work on (adopt none) instead of picking one.
@pytest.mark.parametrize("name", [n for n in packaged_skills() if n not in ("specworks-refine", "specworks-adopt", "specworks-baseline")])
def test_skills_pick_the_change_by_one_shared_rule(name):
    # "Select the change as the other phases do" pointed at no rule; the shared paragraph is that rule.
    text = read_skill(name)
    assert "**Picking the change**" in text and "Pick the change (above)" in text
    assert "as the other phases do" not in text and "as in `/specworks-specify`" not in text


def test_adopt_stops_after_mapping_and_hands_baselines_to_their_own_skill():
    # Baselining every capability up front is the slow, error-prone path; /specworks-baseline runs one capability on request.
    text = read_skill("specworks-adopt")
    assert "specworks capability add <name>" in text and "**End here.**" in text
    assert "## Stage 3" not in text and "specworks new" not in text
    assert "`/specworks-baseline <capability>`" in text


def test_baseline_checks_the_suite_before_creating_its_change():
    text = read_skill("specworks-baseline")
    assert 'specworks new "baseline-<capability>" --json' in text and "/specworks-close" in text
    # A red suite fails the design and code gates; checking it first stops before the change is created.
    assert text.index("specworks run test\n") < text.index('specworks new "baseline-<capability>"')
    # A project with no capabilities is adopted first; the baseline never registers one itself.
    assert "/specworks-adopt" in text.split("## Steps", 1)[1].split("2. **", 1)[0]


def test_close_runs_the_project_commands_once_before_writing():
    # start close (step 1, gate validate) and the real close (step 5) run them; the dry run in between must not.
    text = read_skill("specworks-close")
    assert 'specworks close --change "<ref>" --dry-run --no-run' in text
    assert 'specworks start close --change "<ref>"' in text and '\n   specworks close --change "<ref>"\n' in text


# Every `specworks ...` call a skill shows in code (a span or a fenced block) must be one the CLI
# accepts: a real command and subcommand, real flags, and a known value where a command takes one.
CALL_RE = re.compile(r"(?<![/\w-])specworks ([a-z][a-z-]*(?: [^`\n#]*)?)")
KNOWN_VALUES = {
    "instructions": set(load_artifacts()),
    "gate": set(GATES),
    "start": set(PHASES) - {"done"},
    "phase": set(PHASES) - {"done"},  # `phase` takes the change first, then the phase
    "run": set(COMMAND_KEYS),
}


def code_in(text):
    """The code spans and fenced-block lines of a markdown text."""
    code, inside = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
        elif inside:
            code.append(line)
        else:
            code += re.findall(r"`([^`]+)`", line)
    return code


def skill_calls():
    skills = resources.files("specworks").joinpath("skills")
    for folder in skills.iterdir():
        for doc in (f for f in folder.iterdir() if f.name.endswith(".md")):
            for code in code_in(doc.read_text(encoding="utf-8")):
                yield from ((folder.name, m.group(1).strip()) for m in CALL_RE.finditer(code))


def call_problems(call: str) -> list[str]:
    command = typer.main.get_command(app)
    words = shlex.split(call.replace("|", " "), posix=True) if call.count('"') % 2 == 0 else call.split()
    name, args = words[0], words[1:]
    if name not in command.commands:  # type: ignore[attr-defined]
        return [f"unknown command {name!r}"]
    cmd = command.commands[name]  # type: ignore[attr-defined]
    if hasattr(cmd, "commands") and args:  # a group: spec, task, capability, module
        if args[0] not in cmd.commands:
            return [f"unknown command {name} {args[0]!r}"]
        cmd, args = cmd.commands[args[0]], args[1:]
    options = {opt for param in cmd.params for opt in param.opts}
    problems = [f"{name}: unknown option {word}" for word in args if word.startswith("--") and word.strip("[]") not in options]
    plain = [w for w in args if re.fullmatch(r"[a-z][a-z-]*", w)]  # placeholders (<ref>, "<ref>") and flags are skipped
    if name in KNOWN_VALUES and plain and plain[0] not in KNOWN_VALUES[name]:
        problems.append(f"{name}: unknown value {plain[0]!r}")
    return problems


def test_skills_only_show_cli_calls_that_exist():
    calls = sorted(set(skill_calls()))
    assert len(calls) > 50  # the extraction still finds the skills' calls
    problems = [f"{skill}: specworks {call}: {problem}" for skill, call in calls for problem in call_problems(call)]
    assert problems == []


@pytest.mark.parametrize(
    "call, problem",
    [
        ("chek --change x", "unknown command 'chek'"),
        ("task tick 1.1 --change x", "unknown command task 'tick'"),
        ("gate review --change x --allow-opened", "gate: unknown option --allow-opened"),
        ("instructions proposals --change x", "instructions: unknown value 'proposals'"),
        ('phase "<ref>" implement', "phase: unknown value 'implement'"),
    ],
)
def test_the_skill_call_check_catches_drift(call, problem):
    assert problem in call_problems(call)
