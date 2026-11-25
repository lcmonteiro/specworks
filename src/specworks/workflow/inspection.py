"""
A change's open inspection notes (inspection.md's ``I`` findings), split by whose turn they are.

A note routed to ``inspect`` (``Finding.phase``, REQ-FLOW-010) waits for the reviewer to confirm it; any other open
note waits for the author to work it, at the step it is routed to.
"""

from __future__ import annotations

from dataclasses import dataclass

from specworks.core.changes import Change


@dataclass(frozen=True)
class InspectionNote:
    """
    One open inspection note: its ID (``I1``) and the step it is routed to.

    Implements REQ-FLOW-020.
    """

    id: str
    step: str  # one of the finding steps, or "inspect" for a note waiting for the reviewer


@dataclass(frozen=True)
class InspectionTurns:
    """
    A change's open inspection notes by turn, each list in the order of inspection.md.

    Implements REQ-FLOW-020, REQ-CLI-025.
    """

    author: list[InspectionNote]
    reviewer: list[InspectionNote]

    def __bool__(self) -> bool:
        """
        Any note, for either turn.
        """
        raise NotImplementedError

    def to_dict(self) -> dict:
        """
        ``{"author": [{"id", "step"}], "reviewer": [...]}``, each key only when its list has a note.
        """
        raise NotImplementedError


def inspection_turns(change: Change) -> InspectionTurns:
    """
    The change's open, readable inspection notes by turn (active or archived); none when it has no inspection.md.

    Implements REQ-FLOW-020.
    """
    raise NotImplementedError
