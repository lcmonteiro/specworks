"""Skill peers: one ``SkillPeer`` subclass per packaged skill, each in its own module named after its peer, and their list."""

from __future__ import annotations

from collections.abc import Sequence

from specworks.harness.peers.adopt import AdoptPeer
from specworks.harness.peers.base import MEMORY, MERGE_RULE, PREAMBLE, PREFIX, SkillPeer, peer_name, preamble, skill_instructions
from specworks.harness.peers.baseline import BaselinePeer
from specworks.harness.peers.build import BuildPeer
from specworks.harness.peers.close import ClosePeer
from specworks.harness.peers.code import CodePeer
from specworks.harness.peers.design import DesignPeer
from specworks.harness.peers.done import DonePeer
from specworks.harness.peers.inspect import InspectPeer
from specworks.harness.peers.onboard import OnboardPeer
from specworks.harness.peers.refine import RefinePeer
from specworks.harness.peers.reopen import ReopenPeer
from specworks.harness.peers.review import ReviewPeer
from specworks.harness.peers.specify import SpecifyPeer
from specworks.harness.peers.start import StartPeer
from specworks.harness.peers.test import TestPeer
from specworks.harness.peers.validate import ValidatePeer

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
    InspectPeer,
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
    "InspectPeer",
    "OnboardPeer",
    "RefinePeer",
    "ReopenPeer",
    "ReviewPeer",
    "SpecifyPeer",
    "StartPeer",
    "TestPeer",
    "ValidatePeer",
]
