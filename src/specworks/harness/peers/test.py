"""
The peer ``test``: the ``specworks-test`` skill, the test half of implement.
"""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import SkillPeer


# @req REQ-HARNESS-006
@connector("test")
class TestPeer(SkillPeer):
    """
    The ``specworks-test`` skill as a chat peer; it works in a git worktree of its own. Implements REQ-HARNESS-001, REQ-HARNESS-006.
    """

    worktree = True

    #: Not a pytest test class, though its name starts with ``Test``.
    __test__ = False
