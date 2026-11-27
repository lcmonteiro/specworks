"""
The peer ``autopilot``: the ``specworks-autopilot`` skill, running a change from specify to a passed validate on its own.
"""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import MERGE_RULE, SkillPeer


# @req REQ-HARNESS-004
@connector("autopilot")
class AutopilotPeer(SkillPeer):
    """
    The ``specworks-autopilot`` skill as a chat peer; it merges the test half's worktree like build, so it gets ``MERGE_RULE``.

    Implements REQ-HARNESS-001, REQ-HARNESS-004.
    """

    rules = (MERGE_RULE,)
