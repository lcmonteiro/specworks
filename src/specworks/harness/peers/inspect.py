"""
The peer ``inspect``: the ``specworks-inspect`` skill, walking a change, open or closed, with the reviewer.
"""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import SkillPeer


@connector("inspect")
class InspectPeer(SkillPeer):
    """
    The ``specworks-inspect`` skill as a chat peer. Implements REQ-HARNESS-001.
    """
