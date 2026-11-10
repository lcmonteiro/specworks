"""The peer ``design``: the ``specworks-design`` skill, agreeing a change's API and creating it as stubs."""

from __future__ import annotations

from chatinho import connector

from .base import SkillPeer


@connector("design")
class DesignPeer(SkillPeer):
    """The ``specworks-design`` skill as a chat peer. Implements REQ-HARNESS-001."""
