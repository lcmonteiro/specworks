"""
The peer ``close``: the ``specworks-close`` skill, folding a verified change into the living docs and archiving it.
"""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import SkillPeer


@connector("close")
class ClosePeer(SkillPeer):
    """
    The ``specworks-close`` skill as a chat peer. Implements REQ-HARNESS-001.
    """
