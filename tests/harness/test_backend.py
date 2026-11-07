"""The conversation kept in the change's git-ignored chat.jsonl (REQ-HARNESS-009)."""

from chatinho import LOCAL

from harness.scripted import ScriptedModel, User, chat, git_out, peer_id, read_chat, write_chat
from specworks.core.changes import create_change, load_change
from specworks.core.workspace import load_workspace
from specworks.harness import build_harness

FIELDS = {"id", "from", "to", "replyTo", "status", "text"}


def is_ignored(root, change):
    status = git_out(root, "status", "--porcelain", "--untracked-files=all")
    return "chat.jsonl" not in status and "chat.jsonl" in (change.path / ".gitignore").read_text(encoding="utf-8").splitlines()


# @ac AC-HARNESS-009.1
def test_ac_harness_009_1_appended(project, ws, change):
    session, user = chat(ws, ScriptedModel(script={"refine": ["hello back"]}), request="hello", change=change)
    lines = read_chat(change)
    assert len(lines) >= 2
    said, replied = lines[-2], lines[-1]
    assert FIELDS <= said.keys() and FIELDS <= replied.keys()
    assert said["from"] == LOCAL and said["to"] == peer_id(session, "refine") and said["text"] == "hello"
    assert replied["from"] == peer_id(session, "refine") and replied["replyTo"] == said["id"] and replied["text"] == "hello back"
    assert replied["status"] == "answered"
    assert [m.text for m in user.messages()] == ["hello", "hello back"]
    assert is_ignored(project, change)


def creates_change(root):
    """A step that creates the change `add-x` as a peer would (through `specworks new`), then answers."""

    def step(_messages):
        create_change(load_workspace(root).top.config, "add-x")
        return "created add-x"

    return step


# @ac AC-HARNESS-009.2
def test_ac_harness_009_2_before_the_change_exists(project, ws):
    model = ScriptedModel(script={"refine": [creates_change(project)], "specify": ["specified"]})

    async def more(session, user):
        await user.say("and specify it", to=peer_id(session, "specify"))

    _, user = chat(ws, model, request="add x", then=more)
    lines = read_chat(load_change(load_workspace(project).top.config, "add-x"))
    assert [line["text"] for line in lines] == [m.text for m in user.messages()]
    assert [line["text"] for line in lines] == ["add x", "created add-x", "and specify it", "specified"]


# @ac AC-HARNESS-009.3
def test_ac_harness_009_3_continued(project, ws, change):
    probe = build_harness(ws, ScriptedModel(), change=change, frontend=User())
    refine = peer_id(probe, "refine")
    earlier = [
        {"id": "msg-00000000000000a1", "from": LOCAL, "to": refine, "replyTo": None, "status": "answered", "text": "earlier question", "at": "2026-11-01T10:00:00"},
        {"id": "msg-00000000000000a2", "from": refine, "to": None, "replyTo": "msg-00000000000000a1", "status": "answered", "text": "earlier answer", "at": "2026-11-01T10:00:05"},
    ]
    write_chat(change, earlier)
    model = ScriptedModel(script={"refine": ["new answer"]})
    _, user = chat(ws, model, request="new question", change=change)
    assert [m.text for m in user.messages()][:2] == ["earlier question", "earlier answer"]
    run = model.runs_of("refine")[0]
    assert "earlier question" in run.human and "new question" in run.human
    assert any("earlier answer" in m.text for m in run.messages)
    lines = read_chat(change)
    assert lines[:2] == earlier
    assert [line["text"] for line in lines[2:]] == ["new question", "new answer"]


# @ac AC-HARNESS-009.4
def test_ac_harness_009_4_a_log_that_cannot_be_written(project, ws, change):
    (change.path / "chat.jsonl").mkdir()
    (change.path / "chat.jsonl" / "keep").write_text("x", encoding="utf-8")
    model = ScriptedModel(script={"refine": ["still here"]})
    _, user = chat(ws, model, request="hello", change=change)
    assert model.runs_of("refine"), "the message is delivered"
    assert "still here" in [m.text for m in user.heard]
    folder = change.path / "chat.jsonl"
    assert folder.is_dir() and [p.name for p in folder.iterdir()] == ["keep"]

