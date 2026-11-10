"""Skill peers: one ``SkillPeer`` subclass per packaged skill, each in its own module named after its peer, and their list."""

from __future__ import annotations

from collections.abc import Sequence

from .adopt import AdoptPeer
from .base import MEMORY, MERGE_RULE, PREAMBLE, PREFIX, SkillPeer, peer_name, preamble, skill_instructions
from .baseline import BaselinePeer
from .build import BuildPeer
from .close import ClosePeer
from .code import CodePeer
from .design import DesignPeer
from .done import DonePeer
from .onboard import OnboardPeer
from .refine import RefinePeer
from .reopen import ReopenPeer
from .review import ReviewPeer
from .specify import SpecifyPeer
from .start import StartPeer
from .test import TestPeer
from .validate import ValidatePeer

# @req REQ-HARNESS-001
#: The peer classes, one per packaged skill, in alphabetical order of name. Implements REQ-HARNESS-001.
PEERS: tuple[type[SkillPeer], ...] = (
    AdoptPeer,
    BaselinePeer,
    BuildPeer,
    ClosePeer,
    CodePeer,
    DesignPeer,
    DonePeer,
    OnboardPeer,
    RefinePeer,
    ReopenPeer,
    ReviewPeer,
    SpecifyPeer,
    StartPeer,
    TestPeer,
    ValidatePeer,
)


# @req REQ-HARNESS-006
def worktree_peers(peers: Sequence[type[SkillPeer]] = PEERS) -> frozenset[str]:
    """The names of ``peers`` that work in a git worktree of their own (``worktree``). Implements REQ-HARNESS-006."""
    return frozenset(cls.name for cls in peers if cls.worktree)


__all__ = [
    "MEMORY",
    "MERGE_RULE",
    "PEERS",
    "PREAMBLE",
    "PREFIX",
    "SkillPeer",
    "peer_name",
    "preamble",
    "skill_instructions",
    "worktree_peers",
    "AdoptPeer",
    "BaselinePeer",
    "BuildPeer",
    "ClosePeer",
    "CodePeer",
    "DesignPeer",
    "DonePeer",
    "OnboardPeer",
    "RefinePeer",
    "ReopenPeer",
    "ReviewPeer",
    "SpecifyPeer",
    "StartPeer",
    "TestPeer",
    "ValidatePeer",
]
