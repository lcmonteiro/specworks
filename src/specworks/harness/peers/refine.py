"""The peer ``refine``: the ``specworks-refine`` skill, exploring a problem and recording the refinement."""

from __future__ import annotations

from chatinho import connector

from .base import SkillPeer


@connector("refine")
class RefinePeer(SkillPeer):
    """The ``specworks-refine`` skill as a chat peer. Implements REQ-HARNESS-001."""
