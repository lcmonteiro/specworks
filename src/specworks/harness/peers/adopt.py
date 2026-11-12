"""
The peer ``adopt``: the ``specworks-adopt`` skill, adopting specworks in a project that already has code.
"""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import SkillPeer


@connector("adopt")
class AdoptPeer(SkillPeer):
    """
    The ``specworks-adopt`` skill as a chat peer. Implements REQ-HARNESS-001.
    """
