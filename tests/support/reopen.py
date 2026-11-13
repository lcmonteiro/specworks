"""
Helpers shared by the reopen tests of several capabilities.
"""

from helpers import git
from specworks.core.changes import archived_as, create_change, load_change
from specworks.core.config import load_config
from specworks.specs.merge import archive_change

DAY = "2026-06-01"
EVENTS = '{"event": "phase", "at": "2026-06-01T10:00:00"}\n{"event": "gate", "at": "2026-06-01T10:05:00"}\n'


def make_archived(root, name, abandoned="", day=DAY):
    """
    Archive the change `name` (created when it is not there) as close, or as abandon when `abandoned` has a reason.
    """
    cfg = load_config(root)
    change = load_change(cfg, name) if (cfg.changes_path / name).is_dir() else create_change(cfg, name)
    (change.path / "proposal.md").write_text(f"# Proposal: {name}\n", encoding="utf-8")
    (change.path / "events.jsonl").write_text(EVENTS, encoding="utf-8")
    archive_change(change, cfg.archive_path, day, abandoned=abandoned)
    found = archived_as(cfg, name)
    assert found is not None
    return found


def commit_all(root, message="archive"):
    git(root, "add", "-A")
    git(root, "commit", "-q", "--allow-empty", "-m", message)
