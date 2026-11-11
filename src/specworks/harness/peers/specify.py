"""The peer ``specify``: the ``specworks-specify`` skill, turning a request into a proposal, specs, design and tasks."""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import SkillPeer


@connector("specify")
class SpecifyPeer(SkillPeer):
    """The ``specworks-specify`` skill as a chat peer. Implements REQ-HARNESS-001."""
