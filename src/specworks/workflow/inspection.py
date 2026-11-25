"""
A change's open inspection notes (inspection.md's ``I`` findings), split by whose turn they are.

A note routed to ``inspect`` (``Finding.phase``, REQ-FLOW-010) waits for the reviewer to confirm it; any other open
note waits for the author to work it, at the step it is routed to.
"""

from __future__ import annotations

from dataclasses import dataclass

from specworks.core.changes import Change
from specworks.workflow.artifacts import check_artifact
from specworks.workflow.findings import read_findings

# The step of a note that waits for the reviewer: routed to inspect after ``done in review:`` (REQ-FLOW-010).
REVIEWER_STEP = "inspect"


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
        return bool(self.author or self.reviewer)

    def to_dict(self) -> dict:
        """
        ``{"author": [{"id", "step"}], "reviewer": [...]}``, each key only when its list has a note.
        """
        turns = {"author": self.author, "reviewer": self.reviewer}
        return {turn: [{"id": note.id, "step": note.step} for note in notes] for turn, notes in turns.items() if notes}


# @req REQ-FLOW-020
def inspection_turns(change: Change) -> InspectionTurns:
    """
    The change's open, readable inspection notes by turn (active or archived); none when it has no inspection.md.

    Implements REQ-FLOW-020.
    """
    doc = read_findings(change, check_artifact("inspection"))  # unreadable checkboxes are problems, never findings
    notes = [InspectionNote(id=f.id, step=f.phase) for f in doc.open]
    return InspectionTurns(
        author=[note for note in notes if note.step != REVIEWER_STEP],
        reviewer=[note for note in notes if note.step == REVIEWER_STEP],
    )
