"""
The peer ``start``: the ``specworks-start`` skill, starting a new project from an empty repository.
"""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import SkillPeer


@connector("start")
class StartPeer(SkillPeer):
    """
    The ``specworks-start`` skill as a chat peer. Implements REQ-HARNESS-001.
    """
