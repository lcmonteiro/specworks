"""Build cycles: after a review, where the next design → test → code → review cycle starts.

Each open finding in review.md (``- [ ] R<n> **<type>** ...``) needs work in
one phase: its Decision's ``back to <phase>:`` when it says so, otherwise the
phase its type belongs to (see ``review.parse_review``). The next cycle starts
at the earliest of them and runs every later phase up to review again. A spec
finding is outside the cycle: the change goes back to specify and the build stops.
Once specify has carried it out (``done in specify: ...``), it needs the cycle from
design on, so the build can resume.
"""

from __future__ import annotations

from ..core.changes import Change
from .review import FINDING_PHASES, parse_review, read_review

CYCLE = FINDING_PHASES[1:]  # design, test, code, review
ORDER = FINDING_PHASES


def open_findings(text: str) -> list[dict]:
    """Open findings of a review.md text with their type and the phase that resolves each one."""
    return [f.to_dict() for f in parse_review(text).open]


def next_cycle(change: Change) -> dict:
    """The next build cycle for a reviewed change: where it starts and the phases it runs."""
    review = read_review(change)
    if not review.exists:
        return {"reviewed": False, "open": [], "startAt": None, "phases": [], "handOver": None}
    found = [f.to_dict() for f in review.open]
    if not found:
        return {"reviewed": True, "open": [], "startAt": None, "phases": [], "handOver": None}
    start = min((f["phase"] for f in found), key=ORDER.index)
    if start == "specify":
        return {"reviewed": True, "open": found, "startAt": start, "phases": [], "handOver": "/specworks-specify"}
    return {"reviewed": True, "open": found, "startAt": start, "phases": list(CYCLE[CYCLE.index(start) :]), "handOver": None}
