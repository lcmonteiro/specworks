"""Build cycles: after a review or a validate, the steps the next cycle runs, and the change's next state.

Each open finding of a check artifact (``- [ ] R<n> **<type>** ...`` in review.md,
``V<n>`` in validation.md) needs work in
one step: its Decision's ``back to <step>:`` when it says so, otherwise the
step its type belongs to (see ``findings.parse_findings``). A finding for design
needs design and then both halves of implement (test and code, in parallel),
unless its Decision says ``back to design only:`` (design, then review);
one for implement needs both halves; one for test or code needs only that
half. Every cycle ends with review. A spec finding is outside the cycle: the
change goes back to specify and the build stops. Once specify has carried it
out (``done in specify: ...``), it needs design, so the build can resume.
"""

from __future__ import annotations

from specworks.core.changes import HALVES, PHASES, Change
from specworks.workflow.findings import read_all_findings

#: The steps an open finding waits for outside a build cycle: the check step that confirms it (validate for V, inspect
#: for I). No cycle runs for a finding routed to one of them. Implements REQ-FLOW-012.
WAITING_STEPS = ("validate", "inspect")


# @req REQ-FLOW-012
def next_cycle(change: Change) -> dict:
    """The next build cycle for a reviewed change: the phase it starts at and the steps it runs, from the open findings
    of every check artifact, and ``next``, the change's next state (the phase the cycle starts at; with no cycle, validate
    while a finding waits for it, else the phase after the change's current one; None after close)."""
    docs = read_all_findings(change)
    review = next(doc for doc in docs if doc.artifact.id == "review")
    pending = [f for doc in docs for f in doc.open]
    found = [f.to_dict() for f in pending]
    # A finding routed to validate (``done in review:``) waits for validate to confirm it: no cycle runs for it.
    work = [f for f in pending if f.phase != "validate"]
    needed = {f.phase for f in work}
    steps: list[str] = []
    start = None
    if "specify" in needed:
        start = "specify"
    elif work:
        design = "design" in needed
        # A design-only finding adds no half; any other design finding adds both.
        both = "implement" in needed or any(f.phase == "design" and not f.design_only for f in work)
        halves = [h for h in HALVES if both or h in needed]
        steps = (["design"] if design else []) + halves + ["review"]
        start = "design" if design else "implement" if halves else "review"
    after: str | None
    if start is not None:
        after = start
    elif len(work) < len(pending):
        after = "validate"
    else:
        later = PHASES[PHASES.index(change.phase) + 1 :] if change.phase in PHASES else ()
        after = next((p for p in later if p != "done"), None)
    return {
        "reviewed": review.exists,
        "open": found,
        "startAt": start,
        "phases": steps,
        "handOver": "/specworks-specify" if start == "specify" else None,
        "next": after,
    }
