"""
The peer ``done``: the ``specworks-done`` skill, validating a reviewed change, then closing it.
"""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import SkillPeer


@connector("done")
class DonePeer(SkillPeer):
    """
    The ``specworks-done`` skill as a chat peer. Implements REQ-HARNESS-001.
    """
