"""Helpers shared by the close_phase tests of several capabilities."""

import hashlib

from helpers import REF, run_json

CHANGE_DIR = f".specworks/changes/active/{REF}"


def make_ready(repo):
    """A change that passes validate: implemented, reviewed, in the review phase."""
    (repo / CHANGE_DIR / "review.md").write_text("# Review\n\n## Findings\n\nNone.\n")
    run_json("phase", "review", "--change", REF)
    return repo


def snapshot(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }
