"""The peer ``onboard``: the ``specworks-onboard`` skill, saying where the project stands and what to run next."""

from __future__ import annotations

from chatinho import connector

from specworks.harness.peers.base import SkillPeer


@connector("onboard")
class OnboardPeer(SkillPeer):
    """The ``specworks-onboard`` skill as a chat peer. Implements REQ-HARNESS-001."""
