"""Build cycles: after a review, where the next design → test → code → review cycle starts.

Each open finding in review.md (``- [ ] R<n> **<type>** ...``) needs work in
one phase: its Decision's ``back to <phase>`` when it says so, otherwise the
phase its type belongs to. The next cycle starts at the earliest of them and
runs every later phase up to review again. A spec finding is outside the
cycle: the change goes back to specify and the build stops.
"""

from __future__ import annotations

import re

from ..core.changes import Change
from .review import REVIEW_FILE

CYCLE = ("design", "test", "code", "review")
ORDER = ("specify", *CYCLE)
TYPE_PHASE = {
    "spec-gap": "specify",
    "design-gap": "design",
    "test-gap": "test",
    "code-gap": "code",
    "tag": "code",
    "quality": "code",
}
FINDING_RE = re.compile(r"^\s*- \[(?P<mark>[ xX]?)\]\s+(?P<id>R\d+)\b(?P<text>.*)$")
TYPE_RE = re.compile(r"\*\*(?P<type>[a-z-]+)\*\*")
BACK_RE = re.compile(r"\bback to (?P<phase>specify|design|test|code)\b", re.IGNORECASE)


def open_findings(text: str) -> list[dict]:
    """Open findings with their type and the phase that resolves each one."""
    findings, current = [], None
    for line in text.splitlines():
        match = FINDING_RE.match(line)
        if match:
            current = None
            if match.group("mark").strip():
                continue  # resolved
            type_match = TYPE_RE.search(match.group("text"))
            current = {"id": match.group("id"), "type": type_match.group("type") if type_match else "", "text": match.group("text").strip()}
            current["phase"] = TYPE_PHASE.get(current["type"], "code")
            findings.append(current)
        elif line.startswith("#"):
            current = None
        elif current is not None and (back := BACK_RE.search(line)):
            current["phase"] = back.group("phase").lower()
    return findings


def next_cycle(change: Change) -> dict:
    """The next build cycle for a reviewed change: where it starts and the phases it runs."""
    path = change.path / REVIEW_FILE
    if not path.is_file():
        return {"reviewed": False, "open": [], "startAt": None, "phases": [], "handOver": None}
    found = open_findings(path.read_text(encoding="utf-8"))
    if not found:
        return {"reviewed": True, "open": [], "startAt": None, "phases": [], "handOver": None}
    start = min((f["phase"] for f in found), key=ORDER.index)
    if start == "specify":
        return {"reviewed": True, "open": found, "startAt": start, "phases": [], "handOver": "/specworks-specify"}
    return {"reviewed": True, "open": found, "startAt": start, "phases": list(CYCLE[CYCLE.index(start) :]), "handOver": None}
