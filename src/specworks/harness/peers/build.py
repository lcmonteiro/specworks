"""The peer ``build``: the ``specworks-build`` skill, building a specified change in cycles of design, implement and review."""

from __future__ import annotations

from chatinho import connector

from .base import SkillPeer


@connector("build")
class BuildPeer(SkillPeer):
    """The ``specworks-build`` skill as a chat peer. Implements REQ-HARNESS-001."""
