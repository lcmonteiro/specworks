"""The peer ``review``: the ``specworks-review`` skill, comparing a change's code with its specs."""

from __future__ import annotations

from chatinho import connector

from .base import SkillPeer


@connector("review")
class ReviewPeer(SkillPeer):
    """The ``specworks-review`` skill as a chat peer. Implements REQ-HARNESS-001."""
