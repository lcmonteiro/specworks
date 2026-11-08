"""The conversation kept in the change's git-ignored chat.jsonl (REQ-HARNESS-009)."""

from chatinho import LOCAL

from harness.scripted import ScriptedModel, chat, git_out, peer_id, read_chat, touches, write_chat
from specworks.core.changes import create_change, load_change
from specworks.core.workspace import load_workspace

FIELDS = {"id", "from", "to", "replyTo", "status", "text"}


def is_ignored(root, change):
    status = git_out(root, "status", "--porcelain", "--untracked-files=all")
    return "chat.jsonl" not in status and "chat.jsonl" in (change.path / ".gitignore").read_text(encoding="utf-8").splitlines()


# @ac AC-HARNESS-009.1
def test_ac_harness_009_1_appended(project, ws, change):
    session, user = chat(ws, ScriptedModel(script={"refine": [touches(change, "hello back")]}), say="hello")
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

    _, user = chat(ws, model, say="add x", then=more)
    lines = read_chat(load_change(load_workspace(project).top.config, "add-x"))
    assert [line["text"] for line in lines] == [m.text for m in user.messages()]
    assert [line["text"] for line in lines] == ["add x", "created add-x", "and specify it", "specified"]


# @ac AC-HARNESS-009.4
def test_ac_harness_009_4_a_log_that_cannot_be_written(project, ws, change):
    (change.path / "chat.jsonl").mkdir()
    (change.path / "chat.jsonl" / "keep").write_text("x", encoding="utf-8")
    model = ScriptedModel(script={"refine": [touches(change, "still here")], "specify": ["specified"]})

    async def more(session, user):
        await user.say("and specify it", to=peer_id(session, "specify"))

    _, user = chat(ws, model, say="hello", then=more)
    assert model.runs_of("refine") and model.runs_of("specify"), "every message is delivered"
    assert {"still here", "specified"} <= {m.text for m in user.heard}
    folder = change.path / "chat.jsonl"
    assert folder.is_dir() and [p.name for p in folder.iterdir()] == ["keep"]


EARLIER = [
    {"id": "msg-00000000000000a1", "from": LOCAL, "to": 1, "replyTo": None, "status": "answered", "text": "earlier question", "at": "2026-11-01T10:00:00"},
    {"id": "msg-00000000000000a2", "from": 1, "to": None, "replyTo": "msg-00000000000000a1", "status": "answered", "text": "earlier answer", "at": "2026-11-01T10:00:05"},
]


# @ac AC-HARNESS-009.5
def test_ac_harness_009_5_an_existing_change_continued(project, ws, change):
    write_chat(change, EARLIER)
    model = ScriptedModel(script={"refine": [touches(change, "new answer")]})
    _, user = chat(ws, model, say="new question")
    assert [m.text for m in user.messages()] == ["new question", "new answer"]
    run = model.runs_of("refine")[0]
    assert all("earlier question" not in m.text and "earlier answer" not in m.text for m in run.messages), "the peers' memory does not hold the earlier conversation"
    lines = read_chat(change)
    assert lines[:2] == EARLIER
    assert [line["text"] for line in lines[2:]] == ["new question", "new answer"]


def test_an_untouched_change_is_not_the_runs(project, ws, change):
    # REQ-HARNESS-009: only a change whose folder changes is the run's; the backend's own chat.jsonl does not count.
    write_chat(change, EARLIER)
    _, user = chat(ws, ScriptedModel(script={"refine": ["just talking"]}), say="new question")
    assert [m.text for m in user.messages()] == ["new question", "just talking"]
    assert read_chat(change) == EARLIER
