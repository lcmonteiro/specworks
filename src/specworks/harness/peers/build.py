"""The peer ``build``: the ``specworks-build`` skill, building a specified change in cycles of design, implement and review."""

from __future__ import annotations

from chatinho import connector

from .base import MERGE_RULE, SkillPeer


# @req REQ-HARNESS-004
@connector("build")
class BuildPeer(SkillPeer):
    """The ``specworks-build`` skill as a chat peer; it merges the test half's worktree, so it gets ``MERGE_RULE``.

    Implements REQ-HARNESS-001, REQ-HARNESS-004.
    """

    rules = (MERGE_RULE,)
