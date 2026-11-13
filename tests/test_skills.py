import re
import shlex
from importlib import resources
from pathlib import Path

import pytest
import typer.main

from specworks.cli import app
from specworks.core.changes import PHASES
from specworks.core.config import COMMAND_KEYS, TOOL_IDS
from specworks.tools.skills import TOOLS, ToolError, fill_includes, packaged_skills, read_skill
from specworks.workflow.artifacts import load_artifacts, read_template
from specworks.workflow.gate import GATES
from support.skills import fake_shared, frontmatter, init


def test_the_tool_ids_core_knows_are_the_tools_table():
    # core checks `tools:` without importing tools/skills.py, so the two lists must not drift.
    assert tuple(TOOLS) == TOOL_IDS


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


def test_review_proposes_a_design_only_decision_for_a_design_text_fix():
    # Without it every design finding sends both halves round again, though a reworded Decision changes no test or code.
    text = " ".join(read_skill("specworks-review").split())
    assert "back to design only:" in text and "when the design fix needs no test or code change" in text


def test_build_runs_design_then_review_for_a_design_only_finding():
    text = " ".join(read_skill("specworks-build").split())
    assert "`back to design only:` → design, review" in text


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
COMMITTING = ["specworks-refine", "specworks-specify", "specworks-design", "specworks-test", "specworks-code", "specworks-review", "specworks-validate", "specworks-close"]


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


def test_validate_writes_its_findings_to_validation_md_and_commits():
    # validate is no longer read-only: it keeps validation.md in step with its checks and adds the findings of its reading.
    text = read_skill("specworks-validate")
    assert 'specworks validate --write --change "<ref>"' in text and "--artifact validation" in text
    assert "**Committing**" in text and {"git add", "git commit"} <= set(allowed_commands("specworks-validate"))


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


# refine, adopt and baseline create the change they work on (adopt and start none) instead of picking one; onboard reports every change and picks none;
# reopen picks a closed change, which the rule for active changes does not cover.
@pytest.mark.parametrize(
    "name", [n for n in packaged_skills() if n not in ("specworks-refine", "specworks-adopt", "specworks-baseline", "specworks-start", "specworks-onboard", "specworks-reopen")]
)
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
    """
    One step of the start skill, from its heading up to the next one's.
    """
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
    # Nothing is created before the question: the "Create it" step, which runs every command that writes, comes after it.
    # (Step 2 names `specworks skills --tools` earlier only to say when the tools are saved.)
    question = text.index("Create this structure? (yes/no)")
    assert text.index("**Create it**") > question
    create = start_step(text, "Create it", "Report and hand over")
    for command in ("specworks skills --tools", "specworks module add"):
        assert command in create, command
    assert "specworks init" not in text.split("## Stage 2", 1)[1].split("## Guardrails", 1)[0]  # init has run before start


def test_start_creates_the_structure_with_the_cli_and_a_gitkeep_per_code_folder():
    # init has run before start: `skills --tools` saves the tools chosen in step 2 and installs the skills for them.
    create = start_step(read_skill("specworks-start"), "Create it", "Report and hand over")
    assert re.search(r"specworks skills --tools <[a-z ]+>", create)
    assert "specworks init" not in create
    assert "specworks module add <" in create
    assert ".gitkeep" in create


def test_start_writes_no_language_files():
    # The first change sets up the stack; start writes only the configs, the .gitkeep files and the skills.
    guardrails = flat(read_skill("specworks-start").split("## Guardrails", 1)[1]).lower()
    assert "no language files" in guardrails and "manifest" in guardrails


def test_start_ends_by_handing_over_to_refine():
    steps = flat(read_skill("specworks-start").split("## Guardrails", 1)[0])
    assert "1. /specworks-refine <first change> (recommended)" in steps
    assert "stop here" in steps.lower()


ONBOARD = "specworks-onboard"
ONBOARD_TOOLS = f"Bash(specworks:*), Bash(uv run specworks:*), Bash({UVX}:*), Read, Grep, Glob"
ONBOARD_LINE = "New to specworks? Run **`/specworks-onboard`**: it tells you where your project stands and what to run next, and answers your questions."


def raw_skill(name):
    """
    A packaged skill's SKILL.md as written, its include lines not filled in.
    """
    return resources.files("specworks").joinpath("skills", name, "SKILL.md").read_text(encoding="utf-8")


def test_onboard_is_a_packaged_skill_for_first_time_users():
    # The description decides when an agent loads it: a first-time user asks "how do I get started", not for a phase.
    meta = raw_skill(ONBOARD).split("---\n")[1]
    assert f"name: {ONBOARD}\n" in meta
    description = flat(meta.split("description:", 1)[1].split("allowed-tools:", 1)[0])
    for phrase in ("first time", "getting started", '"onboard"', '"specworks onboard"'):
        assert phrase in description, phrase


def test_onboard_is_read_only_by_its_allowed_tools():
    # The skill diagnoses and explains; with no Write, Edit or git it cannot change the project.
    allowed = re.search(r"^allowed-tools: (.*)$", raw_skill(ONBOARD), re.MULTILINE).group(1).strip()
    assert allowed == ONBOARD_TOOLS
    tools = {tool.strip() for tool in allowed.split(",")}
    assert "Write" not in tools and "Edit" not in tools
    assert "This skill never changes files" in flat(read_skill(ONBOARD))


def test_onboard_uses_the_shared_cli_and_closing_question_text():
    text = raw_skill(ONBOARD)
    assert "<!-- specworks:include running-cli -->\n" in text
    assert "<!-- specworks:include asking-the-user -->\n" in text


def test_onboard_names_the_next_step_for_every_project_state():
    # The state table drifts when a skill is added; every next step it names is pinned.
    text = flat(read_skill(ONBOARD))
    assert "specworks context --json" in text
    for next_step in ("specworks init", "specworks update", "/specworks-start", "/specworks-adopt", "/specworks-baseline",
                  "/specworks-refine", "/specworks-specify", "/specworks-build", "/specworks-done"):
        assert next_step in text, next_step


def test_onboard_answers_from_the_cli_first_and_links_the_wiki():
    text = flat(read_skill(ONBOARD))
    assert "the CLI wins" in text
    assert "https://github.com/lcmonteiro/specworks/wiki" in text


def test_the_readme_quick_start_points_new_users_to_onboard():
    # Just before step 1: the first thing a new user reads after `specworks init`.
    readme = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    quick_start = readme.split("## Quick start", 1)[1].split("\n## ", 1)[0]
    before_step_1, _, _ = quick_start.partition("\n1. ")
    assert ONBOARD_LINE in flat(before_step_1)


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
    # A red suite fails validate; checking it first stops before the change is created.
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
    """
    One numbered step of a skill's Steps, up to the next one.
    """
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


def test_the_tasks_instruction_verifies_a_code_task_without_the_test_half():
    # The code half cannot see the test half's tests until the merge, so a [code] task that waits on them cannot be ticked in its half.
    text = flat(load_artifacts()["tasks"].instruction)
    assert "A [code] task is verified by lint, typecheck or observable behaviour, never by the test half's tests or the suite" in text


def test_the_design_instruction_pins_the_wording_a_change_tests():
    # Both halves read the same phrases from design.md, so the wording tests and the text they check agree at the merge.
    assert "**Pinned wording**" in flat(load_artifacts()["design"].instruction)


def test_the_code_half_ticks_a_task_on_its_own_checks_and_writes_the_pinned_phrases():
    text = flat(read_skill("specworks-code"))
    assert "Tick a [code] task when its own checks pass; the suite is not one of them" in text
    assert "Write the pinned phrases of design.md verbatim" in text


def test_the_test_half_asserts_only_the_pinned_phrases():
    assert "Assert only the pinned phrases of design.md, verbatim" in flat(read_skill("specworks-test"))


def test_specify_fixes_the_check_warnings_about_the_tasks_when_writing_them():
    # The warning is cheapest to act on in specify, before the build; the step pins no phrase, so only its subject is checked.
    tasks_step = flat(step(read_skill("specworks-specify"), 7))
    assert "specworks check" in tasks_step or "`check`" in tasks_step, tasks_step
    assert "warning" in tasks_step, tasks_step


def test_the_design_template_diagrams_comment_follows_the_structural_change_rule():
    diagrams = flat(read_template("design.md").split("## Diagrams", 1)[1].split("\n## ", 1)[0])
    assert "block diagram" in diagrams and "No structural change" in diagrams


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
    """
    The code spans and fenced-block lines of a markdown text.
    """
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


# --- the skills write findings with `specworks finding` ---------------------------


def build_review_step(text):
    return text.split("3. **Review: propose, do not fix**", 1)[1].split("4. **After the review", 1)[0]


def test_review_adds_and_ticks_findings_with_the_finding_commands():
    # Hand-written finding lines drift from what `specworks cycle` reads; the commands write them as the reader expects.
    text = read_skill("specworks-review")
    assert "specworks finding add" in text and "specworks finding close" in text


def test_build_and_the_phase_subagents_write_decisions_with_finding_decide():
    assert "specworks finding decide" in build_review_step(read_skill("specworks-build"))
    shared = resources.files("specworks").joinpath("skills", "_shared", "phase-subagents.md").read_text(encoding="utf-8")
    assert "specworks finding decide" in shared


@pytest.mark.parametrize("name", ["specworks-specify", "specworks-design", "specworks-test", "specworks-code"])
def test_the_steps_record_their_part_with_finding_done(name):
    assert "specworks finding done" in read_skill(name)


def test_the_shared_committing_text_commits_with_specworks_commit():
    # The phases commit through the command, which stages only the files changed since the phase started.
    shared = resources.files("specworks").joinpath("skills", "_shared", "committing.md").read_text(encoding="utf-8")
    assert 'commit with specworks commit --change "<ref>"' in shared


# --- the skills write the config with `specworks config set` ---------------------


def raw_skill_file(path):
    """
    A packaged skill file as written (no shared parts filled in), with its line wraps folded into spaces.
    """
    return " ".join(resources.files("specworks").joinpath("skills", *path.split("/")).read_text(encoding="utf-8").split())


CONFIG_SET_WORDING = [
    ("specworks-test/SKILL.md", 'save it with `specworks config set commands.test "<command>"`'),
    ("specworks-code/SKILL.md", 'save it with `specworks config set commands.test "<command>"`'),
    ("specworks-adopt/SKILL.md", 'write each one with `specworks config set commands.<key> "<command>"`'),
    ("specworks-adopt/SKILL.md", "write it with `specworks config set context --file -` (the text on standard input)"),
    ("specworks-start/SKILL.md", "write it with `specworks config set context --file -` (the text on standard input)"),
    ("specworks-start/SKILL.md", "add `--module \"<name>\"` for a module's own config"),
    ("_shared/phase-subagents.md", '`specworks config set commands.test "<command>"`'),
]
CONFIG_SET_FILES = sorted({path for path, _ in CONFIG_SET_WORDING})


@pytest.mark.parametrize("path, phrase", CONFIG_SET_WORDING)
def test_the_skills_write_the_config_with_config_set(path, phrase):
    # Hand-edited YAML loses the comments or breaks the file; `config set` edits it safely (REQ-CLI-013).
    assert phrase in raw_skill_file(path)


@pytest.mark.parametrize("path", CONFIG_SET_FILES)
def test_the_skills_no_longer_write_commands_or_context_by_hand(path):
    text = raw_skill_file(path)
    assert "under `commands:`" not in text and "under `context:`" not in text


# --- start creates the minimal tree; the first change proposes the capabilities ----------


def test_the_start_skill_creates_the_minimal_tree_with_no_capabilities():
    text = raw_skill_file("specworks-start/SKILL.md")
    assert "the minimal tree: `.specworks/`, `docs/`, `src/` and `tests/`" in text
    assert "No capabilities: the first change proposes them in its refinement, and close registers them." in text


def test_the_start_skill_writes_the_two_gitkeep_files_when_it_creates_the_tree():
    # With no capability no CLI command creates `src/` or `tests/`, and git does not keep empty folders.
    create = flat(start_step(read_skill("specworks-start"), "Create it", "Report and hand over"))
    assert "write an empty `src/.gitkeep` and `tests/.gitkeep`" in create


def test_the_start_skill_never_registers_a_capability():
    text = raw_skill_file("specworks-start/SKILL.md")
    assert "specworks capability add" not in text and "capability add --create" not in text
    guardrails = flat(read_skill("specworks-start").split("## Guardrails", 1)[1])
    assert "No capabilities: start never registers one." in guardrails


def test_the_start_skill_writes_an_architecture_with_no_capabilities_yet():
    create = flat(start_step(read_skill("specworks-start"), "Create it", "Report and hand over"))
    assert "`## Capabilities and how they interact` says `None yet: the first change proposes them.`" in create


ONBOARD_FRESH_ROW = "| `capabilities` and `changes` are empty, and so are `context` and `commands` | set up, nothing mapped |"
ONBOARD_STARTED_ROW = "| `capabilities` and `changes` are empty, and `context` or `commands` is set | started, no capability yet |"


def test_onboard_tells_a_fresh_config_from_a_started_project_with_no_capabilities():
    text = raw_skill_file(f"{ONBOARD}/SKILL.md")
    assert ONBOARD_FRESH_ROW in text and ONBOARD_STARTED_ROW in text
    assert "| `capabilities` is empty |" not in text


def test_onboard_sends_a_started_project_with_no_code_to_refine():
    rows = [flat(line) for line in raw_skill(ONBOARD).splitlines() if ONBOARD_STARTED_ROW in flat(line)]
    assert len(rows) == 1
    assert "`/specworks-refine <first change>` when the repository has no code" in rows[0]


def test_the_refinement_instruction_asks_a_new_capabilitys_module_path_and_description():
    text = flat(load_artifacts()["refinement"].instruction)
    assert "for a new capability say which module should own it, its code path and a one-line description" in text


def test_the_refinement_template_has_a_new_capabilitys_module_and_code_path():
    line = "- `<!-- capability -->`: new (<!-- owning module -->, `<!-- code path -->`) | modified - <!-- what it covers, or why it changes -->"
    assert line in read_template("refinement.md")


def test_refine_proposes_a_new_capabilitys_module_path_and_description():
    guardrails = flat(read_skill("specworks-refine").split("## Guardrails", 1)[1])
    assert "say which module should own each one, its code path and a one-line description" in guardrails


def test_a_key_given_twice_fails():
    # design.md: a key given twice is an error (pinned fragment `gives`).
    text = "<!-- specworks:include record phase=test phase=code -->\n"
    with pytest.raises(ToolError) as error:
        fill_includes(text, "specworks-x", fake_shared({"record": "Record it with --in {{phase}}.\n"}))
    message = str(error.value)
    assert "gives" in message and "phase" in message and "specworks-x" in message and "record" in message


@pytest.mark.parametrize("name", ["specworks-design", "specworks-test", "specworks-code"])
def test_the_back_from_review_rule_is_shared(name):
    assert "<!-- specworks:include back-from-review" in raw_skill_file(f"{name}/SKILL.md")


@pytest.mark.parametrize("name", ["specworks-test", "specworks-code"])
def test_the_start_implement_rule_is_shared(name):
    assert "<!-- specworks:include start-implement" in raw_skill_file(f"{name}/SKILL.md")


def test_specify_looks_up_the_related_requirements_after_listing_the_capabilities():
    # Without the lookup a change can contradict a living requirement that names the same command or flag.
    load = step(read_skill("specworks-specify"), 2)
    assert 'specworks spec find "<term>" ... --json' in load
    assert load.index("specworks spec list --json") < load.index('specworks spec find "<term>" ... --json')
    assert "a MODIFIED block in the delta, or a one-line reason to leave it" in load
    assert "`## Related requirements`" in load


def test_specify_shows_the_related_requirements_when_it_confirms_the_criteria():
    assert "the related requirements, each modified or left with its reason" in step(read_skill("specworks-specify"), 5)


def test_the_proposal_template_has_related_requirements_after_capabilities():
    template = read_template("proposal.md")
    assert "## Related requirements" in template
    assert template.index("## Capabilities") < template.index("## Related requirements")


def test_the_proposal_instruction_asks_for_the_related_requirements():
    assert "**Related requirements**" in load_artifacts()["proposal"].instruction


# --- the skills write and read the module's architecture (project-docs) -------------------

ARCHITECTURE_WORDING = [
    "`<docsPath>/architecture.md`",
    "`<docsPath>/diagrams/architecture-blocks.d2`",
    "## Overview",
    "## Capabilities and how they interact",
    "## Architectural decisions",
    "## Glossary",
    "Keep it to about 150 lines: merge or drop entries rather than grow it.",
    "Update it when the change adds or removes a capability, changes what flows between capabilities, adds a decision that spans capabilities, or adds a term; otherwise leave it as it is.",
    "When it is missing, write it now, before `specworks close`.",
]
READING_ARCHITECTURE_WORDING = (
    "Read the module's `<docsPath>/architecture.md` first (`docsPath` of the module in `specworks context`); when there is none yet, go on without it."
)


@pytest.mark.parametrize("phrase", ARCHITECTURE_WORDING)
def test_the_shared_architecture_text_has_the_structure_and_the_rules(phrase):
    # Close writes the module's architecture from this text; adopt sets it up from it.
    assert phrase in raw_skill_file("_shared/architecture.md")


def test_the_shared_reading_text_reads_the_architecture_first():
    assert READING_ARCHITECTURE_WORDING in raw_skill_file("_shared/reading-architecture.md")


@pytest.mark.parametrize("name", ["specworks-close", "specworks-adopt"])
def test_the_skills_that_write_the_architecture_include_its_shared_text(name):
    assert "<!-- specworks:include architecture -->\n" in raw_skill(name)


def test_start_does_not_include_the_shared_architecture_text():
    # Start's first architecture has no capabilities yet, so it asks for no block diagram.
    assert "<!-- specworks:include architecture -->" not in raw_skill("specworks-start")


@pytest.mark.parametrize("name", ["specworks-refine", "specworks-specify", "specworks-design", "specworks-review", "specworks-onboard"])
def test_the_skills_that_read_the_architecture_include_the_reading_text(name):
    assert "<!-- specworks:include reading-architecture -->\n" in raw_skill(name)


# --- refine starts clear and from the base branch (refine-on-main-and-compact) ---------------

REFINE = "specworks-refine/SKILL.md"
COMPACT_QUESTION = 'ask "Compact the conversation first? (yes/no)"'
BRANCH_QUESTION = 'ask "You are on <branch>, not <base>. Switch to <base>? (yes/no)"'


def test_refine_has_a_before_step_1_section_ahead_of_the_steps():
    # The two stops are a section, not a numbered step, so the step numbers other skills point to do not move.
    text = raw_skill_file(REFINE)
    assert "## Before step 1" in text
    assert text.index("## Before step 1") < text.index("## Steps")


def test_refine_asks_to_compact_a_conversation_that_holds_earlier_work():
    text = raw_skill_file(REFINE)
    assert COMPACT_QUESTION in text
    assert "anything before this request except a summary left by `/compact`" in text


def test_refine_on_yes_tells_the_user_to_compact_and_run_it_again():
    # A skill cannot compact the conversation itself.
    assert "tell the user to run `/compact`, then `/specworks-refine` again with the same request, and stop" in raw_skill_file(REFINE)


def test_refine_goes_straight_on_in_a_new_or_just_compacted_conversation():
    assert "A new or just-compacted conversation goes straight on, without asking." in raw_skill_file(REFINE)


def test_refine_reads_the_branch_with_git_status():
    assert "git status --short --branch" in raw_skill_file(REFINE)


def test_refine_asks_to_switch_to_the_base_branch_and_switches_with_git_switch():
    text = raw_skill_file(REFINE)
    assert BRANCH_QUESTION in text
    assert "git switch <base>" in text


def test_refine_never_switches_a_changed_working_tree():
    assert "When the working tree has changes, say so, stay on the branch and ask nothing." in raw_skill_file(REFINE)


def test_refine_asks_to_compact_before_the_branch_and_both_before_the_steps():
    text = raw_skill_file(REFINE)
    assert text.index(COMPACT_QUESTION) < text.index(BRANCH_QUESTION) < text.index("## Steps")


def test_only_refine_carries_the_compact_and_branch_questions():
    # The other skills run mid-change, where switching to the base branch or compacting is wrong.
    others = [name for name in packaged_skills() if name != "specworks-refine"]
    assert others
    for name in others:
        text = raw_skill_file(f"{name}/SKILL.md")
        assert COMPACT_QUESTION not in text and BRANCH_QUESTION not in text, name


# --- reopen: a closed change goes back to a phase, and why is the problem to start from (add-reopen-change) ---------------
# The skills have no capability, so these tests are untagged and assert only the pinned phrases of design.md, verbatim.
REOPEN = "specworks-reopen"
REOPEN_LINE = "When the change was reopened, the latest reason in specworks status is the problem to start from."


def test_reopen_is_a_packaged_skill_scoped_to_specworks():
    assert REOPEN in packaged_skills()
    meta = raw_skill(REOPEN).split("---\n")[1]
    assert f"name: {REOPEN}\n" in meta
    description = flat(meta.split("description:", 1)[1].split("allowed-tools:", 1)[0])
    use_when = description.split("Use ", 1)[1]
    assert "specworks" in use_when and '"specworks reopen"' in use_when


@pytest.mark.parametrize(
    "phrase",
    [
        'specworks reopen --change "<ref>" --reason "<reason>" --phase <phase>',
        "Reopen <ref> at <phase>? (yes/no)",
        "The reason comes from the user; never invent it.",
        "the earliest phase any of them needs",
        "specworks finding add",
        '--message "<ref>: reopen"',
        "does not switch branches, rebase or push",
    ],
)
def test_the_reopen_skill_carries_its_pinned_wording(phrase):
    assert phrase in flat(read_skill(REOPEN))


@pytest.mark.parametrize("name", ["specworks-refine", "specworks-specify"])
def test_refine_and_specify_start_from_the_latest_reopen_reason(name):
    assert REOPEN_LINE in flat(read_skill(name))


# --- inspect: walk a change, open or closed, with a reviewer, and keep the notes as findings (add-inspect-skill) -----------
# The skills have no capability, so these tests are untagged and assert only the pinned phrases of design.md, verbatim.
INSPECT = "specworks-inspect"


def test_inspect_is_a_packaged_skill_scoped_to_specworks():
    assert INSPECT in packaged_skills()
    meta = raw_skill(INSPECT).split("---\n")[1]
    assert f"name: {INSPECT}\n" in meta
    use_when = flat(meta.split("description:", 1)[1].split("allowed-tools:", 1)[0]).split("Use ", 1)[1]
    assert "specworks" in use_when and '"specworks inspect"' in use_when


@pytest.mark.parametrize("phrase", ["come back later", "stop here", "most uncertain and important first", "at most three hints", "No notes: nothing is written"])
def test_the_inspect_skill_carries_its_pinned_wording(phrase):
    assert phrase in flat(read_skill(INSPECT)).replace("**", "")


def test_inspect_writes_only_through_specworks_finding_and_commit():
    # Read-only git, no Write or Edit: the reviewer's notes reach inspection.md only through the read-back finding writers.
    allowed = re.search(r"^allowed-tools: (.*)$", raw_skill(INSPECT), re.MULTILINE).group(1)
    tools = {tool.strip() for tool in allowed.split(",")}
    assert set(allowed_commands(INSPECT)) == {"specworks", "uv run specworks", UVX, "git diff", "git log", "git status"}
    assert not tools & {"Write", "Edit"}
    text = flat(read_skill(INSPECT))
    assert "--artifact inspection" in text and "specworks finding close I<n>" in text
    assert 'specworks commit --change "<ref>" --message "<ref>: inspect"' in text
    assert "trace --write" in text and "Never run `trace --write`" in text


def test_inspect_hands_its_notes_to_review_or_reopen():
    text = flat(read_skill(INSPECT))
    assert "1. /specworks-review <ref> (recommended)" in text
    assert "1. /specworks-reopen <ref> (recommended): with inspection.md as the problem" in text


def test_review_marks_the_inspection_findings_it_checked_done_in_review():
    # Without the mark an I finding never reaches inspect, and review must never tick it: inspect confirms it.
    text = flat(read_skill("specworks-review"))
    assert 'specworks finding done I<n> --in review --change "<ref>"' in text
