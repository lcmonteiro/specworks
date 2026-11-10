"""The peer ``code``: the ``specworks-code`` skill, the code half of implement."""

from __future__ import annotations

from chatinho import connector

from .base import SkillPeer


@connector("code")
class CodePeer(SkillPeer):
    """The ``specworks-code`` skill as a chat peer. Implements REQ-HARNESS-001."""
