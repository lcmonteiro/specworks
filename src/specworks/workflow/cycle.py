"""
Build cycles: after a review, the steps the next cycle runs.

Each open finding in review.md (``- [ ] R<n> **<type>** ...``) needs work in
one step: its Decision's ``back to <step>:`` when it says so, otherwise the
step its type belongs to (see ``review.parse_review``). A finding for design
needs design and then both halves of implement (test and code, in parallel),
unless its Decision says ``back to design only:`` (design, then review);
one for implement needs both halves; one for test or code needs only that
half. Every cycle ends with review. A spec finding is outside the cycle: the
change goes back to specify and the build stops. Once specify has carried it
out (``done in specify: ...``), it needs design, so the build can resume.
"""

from __future__ import annotations

from specworks.core.changes import HALVES, Change
from specworks.workflow.review import read_review


# @req REQ-FLOW-012
def next_cycle(change: Change) -> dict:
    """
    The next build cycle for a reviewed change: the phase it starts at and the steps it runs.
    """
    review = read_review(change)
    found = [f.to_dict() for f in review.open]
    needed = {f.phase for f in review.open}
    steps: list[str] = []
    start = None
    if "specify" in needed:
        start = "specify"
    elif found:
        design = "design" in needed
        # A design-only finding adds no half; any other design finding adds both.
        both = "implement" in needed or any(f.phase == "design" and not f.design_only for f in review.open)
        halves = [h for h in HALVES if both or h in needed]
        steps = (["design"] if design else []) + halves + ["review"]
        start = "design" if design else "implement" if halves else "review"
    return {
        "reviewed": review.exists,
        "open": found,
        "startAt": start,
        "phases": steps,
        "handOver": "/specworks-specify" if start == "specify" else None,
    }
