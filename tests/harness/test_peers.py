"""Skill peers: one Deep Agent peer per packaged skill, handing work over by message (REQ-HARNESS-001 to REQ-HARNESS-005)."""

import openai
import pytest
from chatinho import LOCAL, HookAnswer, ReplyStatus, declares, name_of

from harness.scripted import ScriptedModel, User, call, chat, peer_id
from specworks.harness.peers import PREFIX, preamble, skill_instructions
from specworks.tools.skills import packaged_skills, read_skill

PEERS = [skill.removeprefix("specworks-") for skill in packaged_skills()]
FILE_TOOLS = {"read_file", "write_file", "edit_file"}

#: The pinned preamble of design.md, verbatim.
PINNED = (
    "You are the peer `{name}` in a specworks harness chat. The other peers are: {peers}.\n"
    "No one types slash commands here: `/specworks-<name>` in your skill means the peer `<name>`.\n"
    "When your skill stops with a question that only offers the next step, take the option marked (recommended) and call hand_over with that peer and the change ref; do not ask the user.\n"
    "When your skill asks the user anything else, call ask_user and wait for the answer.\n"
    "When the recommended option is `stop here`, end without calling hand_over.\n"
    "When your skill merges a worktree's branch, do not merge it yourself: call ask_user asking the user to run `/merge <name>`, and wait."
)


def roster(user):
    return user.peers()


def skill_peers(user):
    """The peers that answer, other than the user, by name."""
    return {name_of(who): who for at, who in roster(user).items() if at != LOCAL and declares(who, HookAnswer)}


def ask(name, text):
    async def then(session, user):
        await user.say(text, to=peer_id(session, name))

    return then


def said_by(session, user, name):
    at = peer_id(session, name)
    return [m for m in user.messages() if m.frm == at]


# --- REQ-HARNESS-001 -------------------------------------------------------------


# @ac AC-HARNESS-001.1
def test_ac_harness_001_1_every_skill_is_a_peer(project, ws):
    user = User()
    session, _ = chat(ws, ScriptedModel(), user=user)
    peers = roster(user)
    assert peers[LOCAL] is user
    assert sorted(skill_peers(user)) == sorted(PEERS)
    assert {"adopt", "baseline", "build", "refine", "test", "validate"} <= set(skill_peers(user))
    assert not any(name.startswith(PREFIX) for name in skill_peers(user))
    others = [who for at, who in peers.items() if at != LOCAL and name_of(who) not in PEERS]
    assert len(others) == 1 and not declares(others[0], HookAnswer), "besides the skills, only the backend, which answers nothing"


# @ac AC-HARNESS-001.2
def test_ac_harness_001_2_the_skill_unchanged(project, ws):
    user = User()
    chat(ws, ScriptedModel(), user=user)
    test = skill_peers(user)["test"]
    instructions = test.options["system_prompt"]
    assert instructions.endswith("\n\n" + read_skill("specworks-test"))
    assert instructions.startswith("You are the peer `test` ")
    assert skill_instructions("specworks-test", PEERS) == preamble("test", PEERS) + "\n\n" + read_skill("specworks-test")


# --- REQ-HARNESS-002 -------------------------------------------------------------


# @ac AC-HARNESS-002.1
def test_ac_harness_002_1_a_question_answered(project, ws):
    model = ScriptedModel(script={"refine": ["done"]})
    session, user = chat(ws, model, then=ask("refine", "what is open?"))
    runs = model.runs_of("refine")
    assert len(runs) == 1
    assert read_skill("specworks-refine") in runs[0].system
    assert runs[0].human[-1] == "what is open?"
    question = next(m for m in user.messages() if m.text == "what is open?")
    assert [m.text for m in user.replies_to(question)] == ["done"]
    assert model.peers_run() == ["refine"]


# @ac AC-HARNESS-002.2
def test_ac_harness_002_2_its_tools(project, ws):
    model = ScriptedModel(script={"build": ["done"]})
    chat(ws, model, then=ask("build", "build add-x"))
    tools = set(model.runs_of("build")[0].tools)
    assert {"hand_over", "ask_test", "ask_code", "ask_user", "run_merge", "run_ws", "ws_run"} <= tools
    assert FILE_TOOLS <= tools
    assert "run_workspace" not in tools, "the /workspace command is gone"
    assert "ask_build" not in tools
    assert {f"ask_{peer}" for peer in PEERS if peer != "build"} <= tools


def auth_error(message):
    import httpx

    response = httpx.Response(401, request=httpx.Request("POST", "http://127.0.0.1:9/v1/chat/completions"))
    return openai.AuthenticationError(message, response=response, body=None)


# @ac AC-HARNESS-002.3
def test_ac_harness_002_3_a_failed_run(project, ws):
    model = ScriptedModel(script={"refine": [auth_error("Incorrect API key provided: sk-live-123")]})
    session, user = chat(ws, model, then=ask("refine", "hello"))
    question = next(m for m in user.messages() if m.text == "hello")
    [reply] = user.replies_to(question)
    assert reply.status is ReplyStatus.ERROR
    assert "AuthenticationError" in reply.text
    assert "sk-live-123" not in reply.text


# --- REQ-HARNESS-003 -------------------------------------------------------------


# @ac AC-HARNESS-003.1
def test_ac_harness_003_1_the_next_peer_starts(project, ws):
    model = ScriptedModel(script={"refine": [call("hand_over", peer="specify", text="specify add-x"), "refined"], "specify": ["specified"]})
    session, user = chat(ws, model, say="add x")
    request = next(m for m in user.messages() if m.text == "add x")
    handed = [m for m in said_by(session, user, "refine") if m.to == peer_id(session, "specify")]
    assert len(handed) == 1
    assert handed[0].text == "specify add-x" and handed[0].reply_to == request.id
    assert model.runs_of("specify") and model.runs_of("specify")[0].human[-1] == "specify add-x"
    assert "handed over to specify" in model.runs_of("refine")[-1].tool_results()
    # the reply of the peer that hands over is posted before the next stage starts
    texts = [m.text for m in user.messages()]
    assert texts.index("refined") < texts.index("specified")


CHAIN = ["refine", "specify", "design", "test", "code", "review", "validate", "close", "done", "baseline", "adopt"]


# @ac AC-HARNESS-003.2
def test_ac_harness_003_2_no_nesting(project, ws):
    script = {a: [call("hand_over", peer=b, text=f"over to {b}"), f"{a} done"] for a, b in zip(CHAIN, CHAIN[1:], strict=False)}
    script[CHAIN[-1]] = [f"{CHAIN[-1]} done"]
    model = ScriptedModel(script=script)
    session, user = chat(ws, model, say="add x")
    assert len(CHAIN) > session.max_depth
    assert model.peers_run() == CHAIN
    assert not [m for m in user.messages() if m.status is ReplyStatus.ERROR]
    assert f"{CHAIN[-1]} done" in [m.text for m in user.messages()]


# @ac AC-HARNESS-003.3
def test_ac_harness_003_3_not_addressed(project, ws):
    model = ScriptedModel(script={"specify": ["specified"]})
    session, user = chat(ws, model, then=ask("specify", "specify add-x"))
    assert model.peers_run() == ["specify"]

    async def to_nobody(session, user):
        await user.say("just thinking aloud")

    model = ScriptedModel()
    chat(ws, model, then=to_nobody)
    assert model.peers_run() == []


# @ac AC-HARNESS-003.4
@pytest.mark.parametrize("target", ["nobody", "refine"], ids=["unknown", "itself"])
def test_ac_harness_003_4_an_unknown_peer(project, ws, target):
    model = ScriptedModel(script={"refine": [call("hand_over", peer=target, text="go"), "stopped"]})
    session, user = chat(ws, model, say="add x")
    result = model.runs_of("refine")[-1].tool_results()[-1]
    assert result.startswith("error:")
    if target == "nobody":
        assert "nobody" in result
    else:
        assert "yourself" in result or "refine" in result
    assert [m.to for m in said_by(session, user, "refine")] == [None], "only its reply, nothing handed over"
    assert model.peers_run() == ["refine"]


# --- REQ-HARNESS-004 -------------------------------------------------------------


# @ac AC-HARNESS-004.1
def test_ac_harness_004_1_the_preamble(project, ws):
    assert preamble("test", ["refine", "specify"]) == PINNED.format(name="test", peers="refine, specify")
    user = User()
    chat(ws, ScriptedModel(), user=user)
    for name, peer in skill_peers(user).items():
        instructions = peer.options["system_prompt"]
        first, *rules = instructions.split("\n\n", 1)[0].splitlines()
        assert first.startswith(f"You are the peer `{name}` in a specworks harness chat. The other peers are: ")
        assert all(other in first for other in PEERS if other != name)
        assert rules == PINNED.splitlines()[1:]


# @ac AC-HARNESS-004.2
def test_ac_harness_004_2_a_question_for_the_user(project, ws):
    model = ScriptedModel(
        script={"refine": [call("ask_user", question="Which option?"), call("hand_over", peer="specify", text="specify option 2"), "refined"], "specify": ["specified"]}
    )
    session, user = chat(ws, model, say="add x", user=User(answers=["option 2"]))
    assert [m.text for m in user.asked] == ["Which option?"]
    assert any("option 2" in r for r in model.runs_of("refine")[1].tool_results())
    texts = [m.text for m in user.messages()]
    assert texts.index("option 2") < texts.index("specify option 2")
    assert model.runs_of("specify")


# --- REQ-HARNESS-005 -------------------------------------------------------------


# @ac AC-HARNESS-005.1
def test_ac_harness_005_1_at_test(project, ws):
    model = ScriptedModel(script={"test": ["added test_empty_file"]})
    session, user = chat(ws, model, then=ask("test", "add a case for an empty file"))
    assert model.peers_run() == ["test"]
    assert model.runs_of("test")[0].human[-1] == "add a case for an empty file"
    question = next(m for m in user.messages() if m.text == "add a case for an empty file")
    assert [m.text for m in user.replies_to(question)] == ["added test_empty_file"]
