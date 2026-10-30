import json
import re
import shlex
import shutil
from importlib import resources

import pytest
import typer.main
from typer.testing import CliRunner

from helpers import init_repo, set_saved_tools
from specworks.cli import app
from specworks.core.changes import PHASES
from specworks.core.config import COMMAND_KEYS, TOOL_IDS, load_config
from specworks.tools.skills import TOOLS, packaged_skills, read_skill, render_skill, resolve_tools, skill_folders, skills_state
from specworks.workflow.artifacts import load_artifacts, read_template
from specworks.workflow.gate import GATES

runner = CliRunner()
SKILL = "specworks-refine"


def init(tmp_path, monkeypatch, *args):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init", *args])
    assert result.exit_code == 0, result.output
    return result.output


def frontmatter(path):
    return path.read_text().split("---\n")[1]


def specworks_skills_in(folder):
    return sorted(p.name for p in folder.iterdir() if p.name.startswith("specworks-")) if folder.is_dir() else []


# @ac AC-INTEG-004.1
def test_no_tool_detected_installs_for_all(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch)
    assert (tmp_path / f".claude/skills/{SKILL}/SKILL.md").is_file()  # Copilot reads .claude/skills/ too
    assert specworks_skills_in(tmp_path / ".github/skills") == [] and not (tmp_path / ".github/prompts").exists()
    assert load_config(tmp_path).tools == ["claude", "copilot"]


def test_the_tool_ids_core_knows_are_the_tools_table():
    # core checks `tools:` without importing tools/skills.py, so the two lists must not drift.
    assert tuple(TOOLS) == TOOL_IDS


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


@pytest.mark.parametrize("name", packaged_skills())
def test_only_build_and_done_run_their_phases_in_subagents(name):
    # A phase run by build or done sees the project and the artifacts, never the chat; a hand-run phase still talks to the user.
    text = read_skill(name)
    chains = name in ("specworks-build", "specworks-done")
    assert ("**Phases in subagents**" in text) is chains
    if chains:
        assert all(f"Result: {kind} <" in text for kind in ("done", "question", "blocked"))
        assert re.search(r"^allowed-tools: .*\bAgent\b", text, re.MULTILINE)


def test_the_subagent_prompt_carries_only_the_phase_the_ref_and_the_skills_folder():
    # Anything else in the prompt (a summary, an answer) is the channel past the artifacts that this rule closes.
    prompt = re.search(r"```\n *(Run the <phase> phase.*?)```", read_skill("specworks-build"), re.DOTALL).group(1)
    assert set(re.findall(r"<([a-z ]+)>", prompt.split("Result:")[0])) == {"phase", "ref", "skills folder"}


def test_a_restarted_phase_uses_the_answer_on_disk_instead_of_asking_again():
    # Without it a fresh design subagent proposes the API again and returns the same question forever.
    text = " ".join(read_skill("specworks-build").split())
    assert "When the answer to a question the skill would ask is already on disk, use it and go on; do not ask it again." in text
    assert "Proposed: waiting for the user's agreement" in text and "Agreed with the user" in text


def test_design_writes_the_proposed_line_and_stubs_only_once_agreed():
    # The build coordinator swaps the line for `Agreed with the user`; a design skill that never writes it leaves the contract one-sided.
    text = " ".join(read_skill("specworks-design").split())
    assert "Proposed: waiting for the user's agreement" in text and "Agreed with the user" in text


def test_the_test_half_fast_forwards_its_worktree_to_the_main_checkout():
    # A worktree can start from an older commit, without design's stubs; the test skill checks, the build skill no longer assumes.
    test = " ".join(read_skill("specworks-test").split())
    assert "git worktree list" in test and "git merge --ff-only" in test
    assert "the worktree starts from HEAD" not in " ".join(read_skill("specworks-build").split())


def test_build_gates_the_review_itself_after_the_decisions():
    # The first review run already ticks the earlier cycle's findings, so a second review subagent after the decisions only re-ran the gate.
    text = " ".join(read_skill("specworks-build").split())
    first_run = text.split("**First run**")[1].split("**You**")[0]
    assert "earlier cycle" in first_run and "- [x]" in first_run
    assert 'run `specworks gate review --change "<ref>" --allow-open` yourself' in text
    assert "fresh review subagent" not in text
    assert "decided `accepted`" not in text


def test_build_review_proposes_every_finding_before_the_user_decides():
    # The user's decisions reach the next review subagent only through review.md.
    text = read_skill("specworks-build")
    assert "**Proposal**:" in text and "**Decision**:" in text


def test_done_closes_only_through_a_second_subagent_after_the_go_ahead():
    # The go-ahead is which fixed prompt is sent, and capability registrations are written to the project first.
    text = " ".join(read_skill("specworks-done").split())
    assert "the merge plan is approved; continue from step 4" in text
    assert "specworks capability add" in text


UVX = "uvx --from git+https://github.com/lcmonteiro/specworks specworks"
COMMITTING = ["specworks-refine", "specworks-specify", "specworks-design", "specworks-test", "specworks-code", "specworks-review", "specworks-close"]


def allowed_commands(name):
    allowed = re.search(r"^allowed-tools: (.*)$", read_skill(name), re.MULTILINE).group(1)
    return re.findall(r"Bash\(([^)]*):\*\)", allowed)


@pytest.mark.parametrize("name", packaged_skills())
def test_skills_pre_approve_only_specworks_and_read_only_git(name):
    # A bare `Bash(uvx:*)` would let the skill run any package without asking; `git push` is never pre-approved.
    commands = allowed_commands(name)
    assert set(commands) <= {"specworks", "uv run specworks", UVX, "git diff", "git log", "git status", "git add", "git commit"}, commands
    assert "git push" not in commands
    assert UVX in commands and f"`{UVX} <cmd>`" in read_skill(name)  # the rule matches the command the skill documents


@pytest.mark.parametrize("name", COMMITTING)
def test_the_skills_that_commit_may_stage_and_commit(name):
    assert {"git add", "git commit"} <= set(allowed_commands(name))


@pytest.mark.parametrize("name", COMMITTING)
def test_each_phase_skill_commits_its_work_after_the_gate(name):
    text = read_skill(name)
    assert "**Committing**" in text and "specworks:include" not in text
    assert "stub, written in the code half" not in text  # the shared text is filled in


def test_validate_is_read_only_and_does_not_commit():
    text = read_skill("specworks-validate")
    assert "**Committing**" not in text and not {"git add", "git commit"} & set(allowed_commands("specworks-validate"))


@pytest.mark.parametrize("name", packaged_skills())
def test_no_skill_stages_everything(name):
    # Staging explicit paths keeps unrelated dirty files out of the phase's commit.
    text = " ".join(read_skill(name).split())
    for found in re.finditer(r"git add -A", text):
        assert text[: found.start()].rstrip(" `").endswith("never"), text[found.start() - 40 : found.end() + 40]
    assert "git add -A &&" not in text and "git add ." not in text


@pytest.mark.parametrize("name", ["specworks-close", "specworks-done"])
def test_close_and_done_ask_before_pushing(name):
    text = " ".join(read_skill(name).split())
    assert "**Pushing**" in text and "Push <branch>? (yes/no)" in text and "git push -u origin <branch>" in text
    assert "stub, written in the code half" not in text


def test_baseline_no_longer_asks_for_a_new_branch():
    # `new` makes the branch.
    assert "preferably on a new branch" not in " ".join(read_skill("specworks-baseline").split())


# refine, adopt and baseline create the change they work on (adopt and start none) instead of picking one.
@pytest.mark.parametrize("name", [n for n in packaged_skills() if n not in ("specworks-refine", "specworks-adopt", "specworks-baseline", "specworks-start")])
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
    assert "`/specworks-baseline <first capability>`" in text


def test_adopt_asks_which_ai_tools_and_passes_them_to_init():
    # init's own question needs a terminal; an agent running adopt has none, so the skill asks and passes --tools.
    text = read_skill("specworks-adopt")
    assert re.search(r"which AI tools", text, re.IGNORECASE)
    assert re.search(r"specworks init --tools <[a-z ]+>", text)
    assert not re.search(r"^\s*specworks init\s*$", text, re.MULTILINE)  # never a bare init that guesses the tools


def test_start_is_a_packaged_skill_that_creates_its_project_instead_of_picking_a_change():
    # Like adopt, start runs before any change exists, so the shared change-picking rule does not apply to it.
    assert "specworks-start" in packaged_skills()
    text = read_skill("specworks-start")
    assert "**Picking the change**" not in text and "Pick the change (above)" not in text


def test_start_refuses_a_set_up_project_and_hands_existing_code_to_adopt():
    # start runs after init (which installs it) and goes on with the fresh config init wrote;
    # a project set up already goes to refine, a repository with code to adopt.
    # The check comes first: everything before the structure is proposed.
    check = flat(read_skill("specworks-start").split("Create this structure? (yes/no)", 1)[0])
    assert "specworks context --json" in check
    assert "/specworks-refine" in check and "/specworks-adopt" in check
    assert "git init" in check  # init refuses outside a git repository
    assert "fresh config" in check and "no capabilities" in check and "no changes" in check
    # With no config (`"root": null`), init has not run: the skill says to run it.
    assert '"root": null' in check and "specworks init" in check


def start_step(text, start, end):
    """One step of the start skill, from its heading up to the next one's."""
    return text.split(f"**{start}**", 1)[1].split(f"**{end}**", 1)[0]


def test_start_recommends_the_tooling_as_options():
    # Only the tooling step: the AI-tools and hand-over options carry a (recommended) of their own.
    tooling = flat(start_step(read_skill("specworks-start"), "Recommend the tooling", "Propose the structure"))
    assert "(recommended)" in tooling
    assert re.search(r"\buv\b[^.]*Python|Python[^.]*\buv\b", tooling)
    assert "CMake" in tooling and "Bazel" in tooling and "C++" in tooling


def test_start_shows_the_tree_and_asks_before_writing():
    text = read_skill("specworks-start")
    assert "Create this structure? (yes/no)" in text
    # Nothing is created before the question: every command that writes comes after it.
    question = text.index("Create this structure? (yes/no)")
    for command in ("specworks skills --tools", "specworks module add", "specworks capability add"):
        assert command in text and text.index(command) > question, command
    assert "specworks init" not in text.split("## Stage 2", 1)[1].split("## Guardrails", 1)[0]  # init has run before start


def test_start_creates_the_structure_with_the_cli_and_a_gitkeep_per_code_folder():
    # init has run before start: `skills --tools` saves the tools chosen in step 2 and installs the skills for them.
    create = start_step(read_skill("specworks-start"), "Create it", "Report and hand over")
    assert re.search(r"specworks skills --tools <[a-z ]+>", create)
    assert "specworks init" not in create
    assert "specworks module add <" in create
    assert re.search(r"specworks capability add <name> --path <[a-z ]+>", create) and "--description" in create
    assert ".gitkeep" in create


def test_start_writes_no_language_files():
    # The first change sets up the stack; start writes only the configs, the .gitkeep files and the skills.
    guardrails = flat(read_skill("specworks-start").split("## Guardrails", 1)[1]).lower()
    assert "no language files" in guardrails and "manifest" in guardrails


def test_start_ends_by_handing_over_to_refine():
    steps = flat(read_skill("specworks-start").split("## Guardrails", 1)[0])
    assert "1. /specworks-refine <first change> (recommended)" in steps
    assert "stop here" in steps.lower()


def test_adopt_baseline_and_close_chain_through_every_capability():
    # After adopt, each capability is baselined and closed in turn; each skill names the next step.
    loop = "for each capability:\n    /specworks-baseline <capability>\n    /specworks-done baseline-<capability>"
    assert loop in read_skill("specworks-adopt") and loop in read_skill("specworks-baseline")
    assert "then\n   `/specworks-baseline` for the next capability" in read_skill("specworks-baseline")
    assert "the next capability with 0 requirements" in read_skill("specworks-close")


def test_done_closes_only_after_validate_passes():
    # done chains the two phase skills; a FAIL must stop it before close changes anything.
    text = read_skill("specworks-done")
    assert "`specworks-validate` and `specworks-close`" in text
    steps = text.split("## Steps", 1)[1]
    assert steps.index("follow `specworks-validate`") < steps.index("follow `specworks-close`")
    assert "**FAIL**" in steps and "Nothing is closed." in steps
    # Running both phases in one go still waits for the go-ahead on the merge plan.
    assert "does not skip it" in text


def test_done_is_validate_then_close():
    # /specworks-validate then /specworks-close must end where /specworks-done ends: done adds no rule of its own
    # (the phase a change may validate from is validate's call), and close refuses what validate's reading failed.
    done = read_skill("specworks-done")
    assert "specworks status" not in done and "specworks start" not in done and "specworks gate" not in done
    assert "It adds no check of its own and skips none." in done
    assert "If validate reported FAIL for this change in this conversation" in read_skill("specworks-close")


def test_baseline_checks_the_suite_before_creating_its_change():
    text = read_skill("specworks-baseline")
    assert 'specworks new "baseline-<capability>" --json' in text and "/specworks-done" in text
    assert "specworks validate" not in text  # validate runs once, in /specworks-done
    # A red suite fails the design and code gates; checking it first stops before the change is created.
    assert text.index("specworks run test\n") < text.index('specworks new "baseline-<capability>"')
    # A project with no capabilities is adopted first; the baseline never registers one itself.
    assert "/specworks-adopt" in text.split("## Steps", 1)[1].split("2. **", 1)[0]


def test_close_runs_the_project_commands_once_before_writing():
    # start close (step 1, gate validate) and the real close (step 5) run them; the dry run in between must not.
    text = read_skill("specworks-close")
    assert 'specworks close --change "<ref>" --dry-run --no-run' in text
    assert 'specworks start close --change "<ref>"' in text and '\n   specworks close --change "<ref>"\n' in text


def flat(text):
    return " ".join(text.split())


def step(text, number):
    """One numbered step of a skill's Steps, up to the next one."""
    return text.split("## Steps", 1)[1].split(f"\n{number}. **", 1)[1].split(f"\n{number + 1}. **", 1)[0]


def test_the_refinement_template_has_outcomes_between_problem_and_context():
    # The outcomes are what the options are weighed against, so they come right after the problem.
    template = read_template("refinement.md")
    assert "## Outcomes" in template
    assert template.index("## Problem") < template.index("## Outcomes") < template.index("## Context")
    options = template.split("## Options", 1)[1].split("## Recommendation", 1)[0]
    assert "outcome" in options.lower()  # each option says which outcomes it meets or fails


def test_the_refinement_instruction_agrees_outcomes_and_paraphrases_its_sources():
    text = flat(load_artifacts()["refinement"].instruction)
    assert "**Outcomes**" in text and "None: <why>" in text
    assert text.index("**Outcomes**") < text.index("**Options**")
    problem = text.split("**Problem**", 1)[1].split("**Outcomes**", 1)[0].lower()
    assert "paraphrase" in problem and "reference" in problem and "individual" in problem
    assert "Quote the user's words" not in text


def test_the_proposal_instruction_covers_every_outcome():
    # Without the rule an agreed outcome can be lost between refinement and specs.
    text = flat(load_artifacts()["proposal"].instruction)
    assert re.search(r"[Ee]very outcome[^.]*requirement[^.]*Out of Scope", text), text
    assert "outcomes" in text.split("**What Changes**", 1)[1].split("**Capabilities**", 1)[0]


def test_refine_agrees_the_outcomes_before_the_options():
    explore = flat(step(read_skill("specworks-refine"), 3)).lower()
    assert "outcome" in explore and explore.index("outcome") < explore.index("option")
    # An outcome that could go more than one way is the user's choice, offered with a recommendation.
    assert "alternatives" in explore and "recommend" in explore


def test_specify_covers_every_outcome_with_a_requirement_or_out_of_scope():
    text = flat(read_skill("specworks-specify"))
    assert re.search(r"[Ee]very outcome[^.]*requirement[^.]*Out of Scope", text)
    assert "outcomes" in flat(step(read_skill("specworks-specify"), 2))


def test_the_design_instruction_asks_a_structural_change_for_a_block_diagram():
    # Architecture lives in design.md: a structural change draws its block diagram, any other says so in one line.
    text = flat(load_artifacts()["design"].instruction)
    reasons = text.split("Sections:", 1)[0]
    assert "component" in reasons and "dependencies" in reasons  # a structural change is a reason to write design.md
    diagrams = text.split("**Diagrams**", 1)[1].split("**Risks / Trade-offs**", 1)[0]
    assert "block diagram" in diagrams and "No structural change" in diagrams


def test_the_design_template_diagrams_comment_follows_the_structural_change_rule():
    diagrams = flat(read_template("design.md").split("## Diagrams", 1)[1].split("\n## ", 1)[0])
    assert "block diagram" in diagrams and "No structural change" in diagrams


@pytest.mark.parametrize("name", packaged_skills())
def test_no_skill_mentions_architecture_md(name):
    # The capability's living design.md carries its block diagram; architecture.md was never written.
    assert "architecture.md" not in read_skill(name)


def test_close_keeps_one_block_diagram_of_the_capability_in_the_living_design():
    living = flat(step(read_skill("specworks-close"), 4))
    assert "one block diagram" in living and "design.md" in living


def test_baseline_draws_a_block_diagram_for_a_capability_with_several_components():
    design = flat(step(read_skill("specworks-baseline"), 5))
    assert "block diagram" in design and "more than one component" in design


def test_specify_draws_diagrams_by_the_structural_change_rule():
    design = flat(step(read_skill("specworks-specify"), 6))
    assert "when they help" not in design
    assert "structural change" in design and "block diagram" in design


def test_the_default_config_names_the_living_docs_without_architecture(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    config = (tmp_path / ".specworks/config.yml").read_text(encoding="utf-8")
    assert "design.md" in config and "architecture.md" not in config


def test_baseline_notes_each_bugs_correct_behaviour_as_the_fix_outcomes():
    # The behaviour the user confirms for a bug is what its fix change must reach.
    text = read_skill("specworks-baseline")
    read = flat(step(text, 3))
    assert "correct behaviour" in read and "alternatives" in read and "recommend" in read
    assert "what was expected instead" not in read
    write = flat(step(text, 4))
    assert "## Outcomes" in write and "confirmed" in write and "alternatives" in write


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
        ('phase "<ref>" code', "phase: unknown value 'code'"),
    ],
)
def test_the_skill_call_check_catches_drift(call, problem):
    assert problem in call_problems(call)


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


MULTILINE = (
    "---\nname: specworks-x\ndescription: >\n  Does x.\n  Use when: the user asks for x.\n"
    "allowed-tools: Bash(specworks:*),\n  Read\n---\n# Body\n"
)


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


def installed_files(root):
    return {p: p.read_text(encoding="utf-8") for d in (".claude", ".github") for p in (root / d).rglob("*") if p.is_file()}


def state_of(root):
    st = skills_state(root, load_config(root).tools)  # as the CLI computes it: with the saved tools
    return st.state, {(f.path, f.reason) for f in st.files}


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


# @ac AC-CLI-009.1
def test_update_refreshes_outdated_skills(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    edited, deleted = (f".claude/skills/{n}/SKILL.md" for n in (SKILL, "specworks-build"))
    (tmp_path / edited).write_text("edited\n", encoding="utf-8")
    (tmp_path / deleted).unlink()
    (tmp_path / ".claude/skills/specworks-propose").mkdir()
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert f"updated {edited}" in result.output and f"updated {deleted}" in result.output
    assert "removed .claude/skills/specworks-propose" in result.output
    assert state_of(tmp_path) == ("current", set())


# @ac AC-CLI-009.2
def test_update_on_current_skills_writes_nothing(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "all")
    before = {p: p.stat().st_mtime_ns for p in installed_files(tmp_path)}
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert "skills up to date" in result.output and "updated" not in result.output
    assert {p: p.stat().st_mtime_ns for p in installed_files(tmp_path)} == before


# @ac AC-CLI-009.3
def test_update_keeps_the_installed_tools(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    set_saved_tools(tmp_path, None)  # a project from before tools were saved
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github/copilot-instructions.md").write_text("# Copilot\n")
    (tmp_path / f".claude/skills/{SKILL}/SKILL.md").write_text("edited\n", encoding="utf-8")
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert f"updated .claude/skills/{SKILL}/SKILL.md" in result.output
    assert not (tmp_path / ".github/skills").exists() and not (tmp_path / ".github/prompts").exists()
    assert load_config(tmp_path).tools == ["claude"]
    assert "tools: [claude]" in (tmp_path / ".specworks/config.yml").read_text(encoding="utf-8")


# @ac AC-CLI-009.5
def test_update_with_both_tools_in_one_folder_is_up_to_date(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude,copilot")
    set_saved_tools(tmp_path, "[claude, copilot]")
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert "skills up to date" in result.output and "updated" not in result.output
    assert specworks_skills_in(tmp_path / ".github/skills") == []


# @ac AC-CLI-009.4
def test_update_from_a_module_updates_the_workspace_root(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    result = runner.invoke(app, ["init", "service", "--no-skills"])
    assert result.exit_code == 0, result.output
    (tmp_path / f".claude/skills/{SKILL}/SKILL.md").write_text("edited\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path / "service")
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0, result.output
    assert f"updated .claude/skills/{SKILL}/SKILL.md" in result.output
    assert not (tmp_path / "service/.claude").exists()
    assert state_of(tmp_path) == ("current", set())


# @ac AC-CLI-004.5
def test_context_shows_the_skills_state(tmp_path, monkeypatch):
    init(tmp_path, monkeypatch, "--tools", "claude")
    data = json.loads(runner.invoke(app, ["context", "--json"]).output)
    assert data["skills"] == {"state": "current", "files": []}
    assert "run specworks update" not in runner.invoke(app, ["context"]).output
    (tmp_path / f".claude/skills/{SKILL}/SKILL.md").write_text("edited\n", encoding="utf-8")
    data = json.loads(runner.invoke(app, ["context", "--json"]).output)
    assert data["skills"] == {"state": "outdated", "files": [{"path": f".claude/skills/{SKILL}/SKILL.md", "reason": "changed"}]}
    assert "skills out of date: run specworks update" in runner.invoke(app, ["context"]).output
