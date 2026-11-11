"""The peer ``reopen``: the ``specworks-reopen`` skill, moving a closed change back to the active ones."""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import SkillPeer


@connector("reopen")
class ReopenPeer(SkillPeer):
    """The ``specworks-reopen`` skill as a chat peer. Implements REQ-HARNESS-001."""
