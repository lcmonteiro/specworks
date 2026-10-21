"""Parse spec markdown: delta specs (in a change) and living specs (next to the code).

Format (shared by both)::

    ## Purpose
    One or two sentences.

    ## ADDED Requirements            <- delta specs; living specs use "## Requirements"

    ### Requirement: REQ-AUTH-001 Users can log in
    The system SHALL ...

    #### Scenario: AC-AUTH-001.1 Valid password
    - **WHEN** ...
    - **THEN** ...

Requirements are keyed by their ID, so a title can change under MODIFIED
without a separate RENAMED section. Acceptance criteria (scenarios) are
numbered under their requirement: AC-<prefix>-<num>.<n>.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# The number is the last segment: `(?![\w-])` stops a prefix with an all-digit segment
# (OAUTH-2) from ending early, so REQ-OAUTH-2-001 is OAUTH-2 number 001, not OAUTH number 2.
REQ_ID_RE = re.compile(r"REQ-(?P<prefix>[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*?)-(?P<num>\d+)(?![\w-])")
AC_ID_RE = re.compile(r"AC-(?P<prefix>[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*?)-(?P<num>\d+)\.(?P<n>\d+)(?![\w-])")
ANY_ID_RE = re.compile(r"\b(?:AC-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*?-\d+\.\d+|REQ-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*?-\d+)(?![\w-])")

H2_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")
REQ_HEADER_RE = re.compile(r"^###\s+Requirement:\s*(?P<rest>.*?)\s*$")
H3_RE = re.compile(r"^###(?!#)\s+\S")
SCENARIO_HEADER_RE = re.compile(r"^####\s+Scenario:\s*(?P<rest>.*?)\s*$")
MISPLACED_SCENARIO_RE = re.compile(r"^(?:#{1,3}|#{5,})\s+Scenario:|^\s*[-*]\s+\**Scenario:", re.IGNORECASE)

DELTA_SECTIONS = ("ADDED", "MODIFIED", "REMOVED")
LIVING_SECTION = "Requirements"
NORMATIVE_RE = re.compile(r"\b(SHALL|MUST)\b")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass
class Scenario:
    id: str | None
    title: str
    line: int
    lines: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.lines).strip()


@dataclass
class Requirement:
    id: str | None
    title: str
    line: int
    section: str  # ADDED / MODIFIED / REMOVED, or "Requirements" in a living spec
    lines: list[str] = field(default_factory=list)  # description: text before the first scenario
    scenarios: list[Scenario] = field(default_factory=list)
    end: int = 0  # last line of the block (before the next requirement or "## " heading)

    @property
    def description(self) -> str:
        return "\n".join(self.lines).strip()

    def markdown(self) -> str:
        """The requirement block as it appears in a spec file."""
        out = [f"### Requirement: {self.id} {self.title}".rstrip(), *self.lines]
        for sc in self.scenarios:
            out += [f"#### Scenario: {sc.id} {sc.title}".rstrip(), *sc.lines]
        return "\n".join(out).strip() + "\n"


@dataclass
class SpecDoc:
    purpose: str = ""
    sections: list[tuple[int, str]] = field(default_factory=list)  # every "## " heading (line, title), in order
    requirements: list[Requirement] = field(default_factory=list)
    problems: list[tuple[int, str]] = field(default_factory=list)  # (line, message) found while parsing

    def section(self, name: str) -> list[Requirement]:
        return [r for r in self.requirements if r.section == name]

    def by_id(self) -> dict[str, Requirement]:
        return {r.id: r for r in self.requirements if r.id}

    def ids(self) -> set[str]:
        """Every requirement and acceptance-criterion ID in the document."""
        return {i for r in self.requirements for i in (r.id, *(s.id for s in r.scenarios)) if i}


def split_id(rest: str, pattern: re.Pattern) -> tuple[str | None, str]:
    """``"REQ-AUTH-001 Users can log in"`` -> ("REQ-AUTH-001", "Users can log in")."""
    match = pattern.match(rest)
    if not match:
        return None, rest.strip()
    return match.group(0), rest[match.end() :].strip(" -:\t")


def section_kind(title: str) -> str | None:
    """Normalise a "## ..." heading to ADDED / MODIFIED / REMOVED / Requirements / Purpose."""
    words = title.split()
    if not words:
        return None
    head = words[0].upper()
    if head in DELTA_SECTIONS and len(words) > 1 and words[1].lower().startswith("requirement"):
        return head
    if title.strip().lower() == "requirements":
        return LIVING_SECTION
    if title.strip().lower() == "purpose":
        return "Purpose"
    return None


# A code fence opens with ``` or ~~~ (three or more) and closes with a run of the same character at least as
# long and nothing after it. A backtick fence's info string has no backtick (```` ``x`` ```` is inline code).
FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


def fenced(lines: list[str]) -> list[bool]:
    """For each line, whether it belongs to a code fence (the fence lines included): examples, not structure."""
    flags, fence = [], ""
    for line in lines:
        match = FENCE_RE.match(line)
        if not fence:
            if match and not (match["fence"][0] == "`" and "`" in match["info"]):
                fence = match["fence"]
            flags.append(bool(fence))
            continue
        if match and match["fence"][0] == fence[0] and len(match["fence"]) >= len(fence) and not match["info"].strip():
            fence = ""
        flags.append(True)
    return flags


def blank_comments(text: str) -> str:
    """``text`` with its HTML comments (template hints) blanked out, keeping line numbers."""
    return COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def h2_titles(text: str) -> list[str]:
    """The level-2 (``##``) headings of a markdown text, outside code fences and HTML comments."""
    lines = blank_comments(text).splitlines()
    return [m.group("title") for line, example in zip(lines, fenced(lines), strict=True) if not example and (m := H2_RE.match(line))]


# @req REQ-SPECS-004
def parse_spec(text: str) -> SpecDoc:
    doc = SpecDoc()
    section: str | None = None
    purpose: list[str] = []
    req: Requirement | None = None
    scenario: Scenario | None = None
    # HTML comments (template hints) are not part of a spec.
    lines = blank_comments(text).splitlines()
    in_fence = fenced(lines)

    def close_block(last: int) -> None:
        if req is not None:
            req.end = last

    for number, line in enumerate(lines, start=1):
        if in_fence[number - 1]:
            target = scenario.lines if scenario else req.lines if req else purpose if section == "Purpose" else None
            if target is not None:
                target.append(line)
            continue

        if h2 := H2_RE.match(line):
            doc.sections.append((number, h2.group("title")))
            close_block(number - 1)
            section = section_kind(h2.group("title"))
            req = scenario = None
            continue
        if header := REQ_HEADER_RE.match(line):
            scenario = None
            close_block(number - 1)
            if section not in (*DELTA_SECTIONS, LIVING_SECTION):
                doc.problems.append((number, "requirement outside an ADDED/MODIFIED/REMOVED (or Requirements) section"))
            req_id, title = split_id(header.group("rest"), REQ_ID_RE)
            req = Requirement(id=req_id, title=title, line=number, section=section or "")
            doc.requirements.append(req)
            continue
        if header := SCENARIO_HEADER_RE.match(line):
            sc_id, title = split_id(header.group("rest"), AC_ID_RE)
            scenario = Scenario(id=sc_id, title=title, line=number)
            if req is None:
                doc.problems.append((number, "scenario outside a requirement"))
            else:
                req.scenarios.append(scenario)
            continue
        if H3_RE.match(line) and not MISPLACED_SCENARIO_RE.match(line) and section in (*DELTA_SECTIONS, LIVING_SECTION):
            # Another "### " heading ends the requirement before it: replacing or removing that
            # block at close must not take the heading and its text along.
            close_block(number - 1)
            req = scenario = None
            doc.problems.append(
                (number, f"'{line.strip()}' is not a requirement: a requirements section holds only '### Requirement:' blocks "
                         "(use '####' inside a requirement, or a '## ' section of its own)")
            )
            continue
        if MISPLACED_SCENARIO_RE.match(line):
            doc.problems.append((number, "scenario headers must use exactly four hashes: '#### Scenario: AC-... title'"))

        if scenario is not None:
            scenario.lines.append(line)
        elif req is not None:
            req.lines.append(line)
        elif section == "Purpose":
            purpose.append(line)

    close_block(len(lines))
    doc.purpose = "\n".join(purpose).strip()
    return doc


def requirement_number(req_id: str) -> int:
    match = REQ_ID_RE.fullmatch(req_id)
    return int(match.group("num")) if match else 0


# @req REQ-SPECS-004
def id_prefix(any_id: str) -> str | None:
    """``REQ-BILLING-INVOICES-001`` / ``AC-BILLING-INVOICES-001.2`` -> ``BILLING-INVOICES``; None if not an ID.

    The number is the last segment, so a prefix that extends another one
    (``BILLING`` / ``BILLING-INVOICES``) is never mistaken for it.
    """
    match = REQ_ID_RE.fullmatch(any_id) or AC_ID_RE.fullmatch(any_id)
    return match.group("prefix") if match else None


def ac_parent(ac_id: str) -> str | None:
    """``AC-AUTH-001.2`` -> ``REQ-AUTH-001``."""
    match = AC_ID_RE.fullmatch(ac_id)
    return f"REQ-{match.group('prefix')}-{match.group('num')}" if match else None


def find_ids(text: str) -> list[str]:
    """Every REQ-/AC- ID mentioned in ``text``, in order of appearance."""
    return [m.group(0) for m in ANY_ID_RE.finditer(text)]


# @req REQ-SPECS-012, REQ-SPECS-013
def table_cell(text: str) -> str:
    """``text`` for a markdown table cell: a ``|`` escaped so it doesn't end the cell."""
    return text.replace("|", "\\|")


# @req REQ-SPECS-004
def living_problems(doc: SpecDoc) -> list[tuple[int, str]]:
    """(line, message) for each way a living spec is not one ``close`` can merge into or index."""
    problems = list(doc.problems)
    seen: dict[str, int] = {}

    def once(any_id: str, line: int) -> None:
        if any_id in seen:
            problems.append((line, f"{any_id} is used twice (line {seen[any_id]})"))
        seen.setdefault(any_id, line)

    for req in doc.requirements:
        if req.section != LIVING_SECTION:
            problems.append((req.line, f"requirement outside '## {LIVING_SECTION}'"))
        if req.id is None:
            problems.append((req.line, "requirement header has no 'REQ-<prefix>-NNN' ID"))
            continue
        once(req.id, req.line)
        if not NORMATIVE_RE.search(req.description):
            problems.append((req.line, f"{req.id}: state the requirement with SHALL or MUST"))
        if not req.scenarios:
            problems.append((req.line, f"{req.id} has no '#### Scenario: AC-...' (acceptance criterion)"))
        for sc in req.scenarios:
            if sc.id is None:
                problems.append((sc.line, f"scenario of {req.id} has no 'AC-<prefix>-NNN.<n>' ID"))
                continue
            once(sc.id, sc.line)
            if ac_parent(sc.id) != req.id:
                problems.append((sc.line, f"{sc.id} is under {req.id}"))
    return sorted(problems)
