"""The peer ``baseline``: the ``specworks-baseline`` skill, recording a capability's existing behaviour as requirements."""

from __future__ import annotations

from chatinho import connector

from .base import SkillPeer


@connector("baseline")
class BaselinePeer(SkillPeer):
    """The ``specworks-baseline`` skill as a chat peer. Implements REQ-HARNESS-001."""
