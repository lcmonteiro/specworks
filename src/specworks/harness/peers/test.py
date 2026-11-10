"""The peer ``test``: the ``specworks-test`` skill, the test half of implement."""

from __future__ import annotations

from chatinho import connector

from .base import SkillPeer


@connector("test")
class TestPeer(SkillPeer):
    """The ``specworks-test`` skill as a chat peer. Implements REQ-HARNESS-001."""

    #: Not a pytest test class, though its name starts with ``Test``.
    __test__ = False
