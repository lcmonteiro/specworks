"""
The peer ``validate``: the ``specworks-validate`` skill, the read-only pass/fail check before close.
"""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import SkillPeer


@connector("validate")
class ValidatePeer(SkillPeer):
    """
    The ``specworks-validate`` skill as a chat peer. Implements REQ-HARNESS-001.
    """
