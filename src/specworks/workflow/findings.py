"""
Findings of a change's check artifacts (review.md, validation.md, inspection.md): reading them, routing them, and writing them.

A check artifact (``artifacts.CheckArtifact``) holds findings whose IDs start with its letter (``R1`` in review.md,
``V1`` in validation.md, ``I1`` in inspection.md). Every one is read the same way and written by the same commands, which read their edit
back before the file is written.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from specworks.core.changes import Change
from specworks.core.errors import SpecworksError
from specworks.core.files import read_text
from specworks.specs.specfile import H2_RE, blank_comments, fenced
from specworks.workflow.artifacts import CheckArtifact, WorkflowError, check_artifact, check_artifact_for, check_artifacts, read_template

# --- reading findings ----------------------------------------------------------
#
# Findings are checkboxes (``- [ ] R<n> **<type>** ...``, ``- [x]`` once resolved);
# lines indented under one belong to it (its Decision). A Decision saying
# ``back to <step>: <proposal>`` sends the finding to that step (specify, design,
# implement, test, code or review), and ``back to design only:`` to design and then
# straight to review; otherwise its type decides. A step that carried out the
# proposal adds ``done in <step>: <what changed>``: the finding stays open until
# the step that found it confirms it, but the work left is in the steps after that
# one (after review, validate). Untagged changed files are accounted for under their
# own heading in review.md.

# The step that resolves each finding type, in workflow order (specify comes first).
TYPE_PHASE = {
    "spec-gap": "specify",
    "design-gap": "design",
    "test-gap": "test",
    "code-gap": "code",
    "tag": "code",
    "quality": "code",
    "question": "review",
}
# A finding is a checkbox with its ID first, the artifact's letter and a number: ``- [ ] R1 ...``
# in review.md; ``*``/``+``/``1.`` bullets and a bold ``**R1**`` are read too. Any other checkbox
# (another letter included) is reported, never skipped: a finding the parser cannot see would let
# the gate pass with it open.
FINDING_PATTERN = r"^\s*(?:[-*+]|\d+[.)])\s+\[(?P<mark>[ xX]?)\]\s+(?P<bold>\*\*)?(?P<id>{letter}\d+)\b(?(bold)\*\*)(?P<text>.*)$"
FINDING_RE = re.compile(FINDING_PATTERN.format(letter="R"))  # review.md's


# @req REQ-FLOW-018
@cache
def _finding_re(letter: str) -> re.Pattern[str]:
    """
    ``FINDING_RE`` for a check artifact's letter: a checkbox with another letter's ID is not one of its findings.
    """
    return re.compile(FINDING_PATTERN.format(letter=re.escape(letter)))
CHECKBOX_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s*\[[^\]]?\]")
TYPE_RE = re.compile(r"\*\*([A-Za-z_-]+)\*\*")
BACK_RE = re.compile(r"\bback to (?P<phase>specify|design|implement|test|code|review)(?P<only>\s+only)?\s*:", re.IGNORECASE)
DONE_RE = re.compile(r"\bdone in (?P<phase>specify|design|implement|test|code|review)\s*:", re.IGNORECASE)
# The ``**Check**`` line under a finding validate wrote: the key of the check it was written for (REQ-FLOW-019).
CHECK_LINE_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*Check\*\*\s*:\s*(?P<check>\S.*?)\s*$")
# The steps a finding can be routed to, in workflow order: implement is both halves, test and code one each.
FINDING_STEPS = ("specify", "design", "implement", "test", "code", "review")
# The step a finding needs once a step carried out its proposal (``done in <step>:``).
# After review, a finding another check artifact holds waits for the step that found it (validate, inspect: ``_next_step``).
NEXT_STEP = {"specify": "design", "design": "implement", "implement": "review", "test": "review", "code": "review", "review": "validate"}


# Where a line's text starts: after its indentation and an optional bullet, or after a bold label there too
# (``**Decision**:``, ``**Decision:**``, ``**Fix**``). A route form counts only there (REQ-FLOW-010).
_BULLET = r"^\s*(?:(?:[-*+]|\d+[.)])\s+)?"
LINE_STARTS = (re.compile(_BULLET), re.compile(_BULLET + r"\*\*[A-Za-z][\w' -]*(?:\*\*\s*:?|\s*:\*\*)\s*"))


# @req REQ-FLOW-010
def _line_start(line: str, form: re.Pattern[str]) -> re.Match[str] | None:
    """
    ``form`` where ``line``'s text starts (after the bullet, or after a bold label), else None: later on the line it is text.
    """
    for start in LINE_STARTS:
        if (prefix := start.match(line)) and (found := form.match(line, prefix.end())):
            return found
    return None


# @req REQ-FLOW-010
def _route(line: str) -> tuple[str, bool] | None:
    """
    The step a ``back to <step>:`` starting ``line``'s text routes to, and whether it is ``back to design only:``;
    None when it has none. ``only`` after any other step is not a route.
    """
    back = _line_start(line, BACK_RE)
    if back is None:
        return None
    phase = back.group("phase").lower()
    return (phase, bool(back.group("only"))) if not back.group("only") or phase == "design" else None


# @req REQ-FLOW-010
def _done_in(line: str) -> str | None:
    """
    The step of a ``done in <step>:`` starting ``line``'s text, else None.
    """
    carried = _line_start(line, DONE_RE)
    return carried.group("phase").lower() if carried else None


# @req REQ-FLOW-010
def _next_step(done_in: str, design_only: bool = False, artifact: CheckArtifact | None = None) -> str:
    """
    The step a finding needs once ``done_in`` carried out its proposal: review after design for a design-only finding.
    After review, the step of the finding's check ``artifact`` when that is not review (validate for V, inspect for I),
    else validate; ``None``: validate after review, as before.

    Implements REQ-FLOW-010.
    """
    if done_in == "review" and artifact is not None and artifact.phase != "review":
        return artifact.phase
    return "review" if design_only and done_in == "design" else NEXT_STEP[done_in]

ACCOUNTED_SECTION = "changed files without tags"


@dataclass
class Finding:
    id: str
    done: bool
    type: str  # "" when the finding names none
    text: str  # the finding's line, after its ID
    phase: str  # the step that resolves it, one of FINDING_STEPS (after ``done_in``, the next one: after review, validate or inspect)
    routed: bool = True  # False: neither a known type nor a "back to"/"done in" step, so ``phase`` is only a guess
    done_in: str = ""  # the step that carried out its proposal (``done in <step>:``), awaiting review
    design_only: bool = False  # its Decision says ``back to design only:``: after design it goes to review (REQ-FLOW-010)
    check: str = ""  # its ``**Check**`` line: the key of the validate check it was written for (REQ-FLOW-019)

    def to_dict(self) -> dict:
        data: dict = {"id": self.id, "type": self.type, "text": self.text, "phase": self.phase}
        if self.done_in:
            data["doneIn"] = self.done_in
        if self.design_only:
            data["designOnly"] = True
        return data


@dataclass
class FindingsDoc:
    """
    A check artifact's findings as read; ``accounted`` and ``accounts_for`` are review.md's only (empty elsewhere).
    """

    exists: bool
    artifact: CheckArtifact
    findings: list[Finding] = field(default_factory=list)
    accounted: str = ""  # text of "## Changed files without tags"
    problems: list[str] = field(default_factory=list)  # checkbox lines that are not readable findings

    @property
    def open(self) -> list[Finding]:
        return [f for f in self.findings if not f.done]

    def accounts_for(self, path: str) -> bool:
        """
        ``path`` appears as a whole path under "Changed files without tags" (``src/a.py``, not ``src/a.py.bak``).
        """
        return re.search(rf"(?<![\w./-]){re.escape(path)}(?![\w./-])", self.accounted) is not None


# @req REQ-FLOW-010
def parse_findings(text: str, artifact: CheckArtifact) -> FindingsDoc:
    """
    Findings of a check artifact's text (IDs with its letter), and review.md's "Changed files without tags" section;
    HTML comments and code fences are ignored.

    Implements REQ-FLOW-010, REQ-FLOW-018.
    """
    finding_re = _finding_re(artifact.letter)
    doc = FindingsDoc(exists=True, artifact=artifact)
    current: Finding | None = None
    section = ""
    accounted: list[str] = []
    # Comments are blanked line for line, so reported line numbers stay those of the file.
    lines = blank_comments(text).splitlines()
    for number, (line, example) in enumerate(zip(lines, fenced(lines), strict=True), start=1):
        if example:  # a finding shown in a code fence is an example; a fence under a finding stays in it
            if section == ACCOUNTED_SECTION:
                accounted.append(line)
            continue
        if h2 := H2_RE.match(line):
            section, current = h2.group("title").strip().lower(), None
            continue
        if section == ACCOUNTED_SECTION:
            accounted.append(line)
            continue
        if match := finding_re.match(line):
            body = match.group("text").strip()
            # The first bold word that is a type (any case); else the first bold word, reported below as unknown.
            bold = [word.lower() for word in TYPE_RE.findall(body)]
            kind = next((word for word in bold if word in TYPE_PHASE), bold[0] if bold else "")
            current = Finding(
                id=match.group("id"),
                done=bool(match.group("mark").strip()),
                type=kind,
                text=body,
                phase=TYPE_PHASE.get(kind, "code"),
                routed=kind in TYPE_PHASE,
            )
            doc.findings.append(current)
            continue  # the finding's own line is text: a form it quotes never routes it
        if CHECKBOX_RE.match(line) and (current is None or not line.startswith((" ", "\t"))):
            # Indented under a finding, it is part of that finding (a sub-step); anywhere else it could hide open work.
            doc.problems.append(f"line {number}: {line.strip()!r} is not a finding; write it as '- [ ] {artifact.letter}<n> **<type>** ...'")
            current = None
        elif current is not None and line.strip() and not line.startswith((" ", "\t")):
            current = None  # back at the top level: the finding's block has ended
        if current is not None and (back := _route(line)):
            (current.phase, current.design_only), current.routed = back, True
        if current is not None and (carried := _done_in(line)):
            current.done_in, current.routed = carried, True
        if current is not None and not current.check and (check := CHECK_LINE_RE.match(line)):
            current.check = check.group("check")
    for finding in doc.findings:
        if finding.done_in:
            finding.phase = _next_step(finding.done_in, finding.design_only, artifact)
        if not finding.done and not finding.routed:
            # The next build cycle starts from each open finding's phase, so it is never guessed.
            doc.problems.append(
                f"{finding.id}: type {finding.type or '(none)'!r} is not one of {', '.join(TYPE_PHASE)}; "
                f"name one, or add a Decision 'back to <specify|design|implement|test|code|review>: ...'"
            )
    doc.accounted = "\n".join(accounted)
    return doc


def read_findings(change: Change, artifact: CheckArtifact) -> FindingsDoc:
    """
    The check artifact's findings in the change; ``exists=False`` when its file is missing.
    """
    path = change.path / artifact.file
    return parse_findings(read_text(path), artifact) if path.is_file() else FindingsDoc(exists=False, artifact=artifact)


def read_all_findings(change: Change) -> list[FindingsDoc]:
    """
    The findings of every check artifact of the change, in schema order (a missing file reads with ``exists=False``).

    Implements REQ-FLOW-018, REQ-FLOW-012.
    """
    return [read_findings(change, artifact) for artifact in check_artifacts()]


# --- writing findings ----------------------------------------------------------
#
# Each writer edits a check artifact's text in place (one line added at the end of
# the finding's block, a Decision replaced, a box ticked), reads the edited text back
# with ``parse_findings``, and writes the file only when the finding reads as expected.



# A Decision line under a finding, as written by hand (``- **Decision**: ...``) or by ``decide_finding``.
DECISION_LINE_RE = re.compile(r"^(?P<indent>\s*)(?:[-*+]|\d+[.)])\s+\**Decision\**\s*:", re.IGNORECASE)
DECISION_RE = re.compile(r"^(?:back to (?:specify|design|implement|test|code|review)|back to design\s+only|accepted)\s*:\s*\S", re.IGNORECASE)
DECISION_FORM = "a decision starts with 'back to <step>:' (specify, design, implement, test or code), 'back to design only:' or 'accepted:'"
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
CHECKBOX_MARK_RE = re.compile(r"\[[ xX]?\]")


class FindingError(SpecworksError):
    """
    A refused write to a check artifact: an unknown artifact, finding, type or step, an empty text, a decision in
    another form, or an edit that does not read back; the file is named and left as it was.
    """


@dataclass
class _Block:
    start: int  # the finding's checkbox line
    end: int  # its last non-blank line
    indent: str  # the checkbox line's own indentation


@dataclass
class _Review:
    """
    A check artifact split into lines (each with its own ending), where its findings and the Findings section are.
    """

    path: Path
    artifact: CheckArtifact
    lines: list[str]
    newline: str
    blocks: dict[str, _Block] = field(default_factory=dict)
    section: tuple[int, int] | None = None  # the "## Findings" heading and the line after its last one
    decisions: dict[str, list[int]] = field(default_factory=dict)  # the Decision lines under each finding

    @property
    def text(self) -> str:
        return "".join(self.lines)


# @req REQ-FLOW-016
def _locate(path: Path, text: str, artifact: CheckArtifact) -> _Review:
    """
    Where each finding's block is, read the way ``parse_findings`` reads it (comments blanked, fences ignored).
    """
    review = _Review(path, artifact, text.splitlines(keepends=True), "\r\n" if "\r\n" in text else "\n")
    lines = blank_comments(text).splitlines()
    current: _Block | None = None
    owner: str | None = None  # the ID of the finding ``current`` is, when it is the one kept in ``blocks``
    section = ""
    for number, (line, example) in enumerate(zip(lines, fenced(lines), strict=True)):
        indented = line.startswith((" ", "\t"))
        if example:  # a fence indented under a finding is part of it
            if current is not None and indented:
                current.end = number
            continue
        if h2 := H2_RE.match(line):
            if section == "findings" and review.section:
                review.section = (review.section[0], number)
            section, current = h2.group("title").strip().lower(), None
            if section == "findings" and review.section is None:
                review.section = (number, len(lines))
            continue
        if section == ACCOUNTED_SECTION:
            continue
        if match := _finding_re(artifact.letter).match(line):
            current = _Block(number, number, line[: len(line) - len(line.lstrip())])
            owner = match.group("id") if match.group("id") not in review.blocks else None  # a repeated ID: the first one is the finding
            review.blocks.setdefault(match.group("id"), current)
            continue
        if (CHECKBOX_RE.match(line) and (current is None or not indented)) or (current is not None and line.strip() and not indented):
            current = None
        if current is not None and line.strip():
            current.end = number
            if owner is not None and DECISION_LINE_RE.match(line):
                review.decisions.setdefault(owner, []).append(number)
    return review


def _artifact(find: Callable[[], CheckArtifact]) -> CheckArtifact:
    """
    The check artifact ``find`` names, its ``WorkflowError`` (an unknown artifact or ID, naming the check artifacts) as a ``FindingError``.
    """
    try:
        return find()
    except WorkflowError as exc:
        raise FindingError(str(exc)) from None


def _one_line(value: str, what: str) -> str:
    text = " ".join(value.split())
    if not text:
        raise FindingError(f"the {what} is empty")
    return text


def _open(change: Change, artifact: CheckArtifact) -> tuple[Path, str]:
    path = change.path / artifact.file
    return path, read_text(path, keep_newlines=True) if path.is_file() else ""


def _find(review: _Review, finding_id: str) -> tuple[str, _Block]:
    fid = finding_id.strip().upper()
    if fid not in review.blocks:
        raise FindingError(f"no finding {finding_id.strip()} in {review.path}")
    return fid, review.blocks[fid]


def _insert(review: _Review, at: int, new: list[str]) -> None:
    """
    Insert ``new`` lines before line ``at``, each ending with the file's own newline.
    """
    if at > 0 and not review.lines[at - 1].endswith(("\n", "\r")):
        review.lines[at - 1] += review.newline
    review.lines[at:at] = [line + review.newline for line in new]


def _tick(review: _Review, block: _Block) -> None:
    review.lines[block.start] = CHECKBOX_MARK_RE.sub("[x]", review.lines[block.start], count=1)


def _write(review: _Review, original: str, fid: str, expect: dict[str, object]) -> Finding:
    """
    Write the edited file only when ``fid`` reads back as ``expect`` and every other finding as before.
    """
    artifact = review.artifact
    before = parse_findings(original, artifact) if original else FindingsDoc(exists=False, artifact=artifact)
    after = parse_findings(review.text, artifact)
    others_before = [(f.id, f.done, f.type, f.text, f.phase, f.done_in, f.design_only) for f in before.findings if f.id != fid]
    others_after = [(f.id, f.done, f.type, f.text, f.phase, f.done_in, f.design_only) for f in after.findings if f.id != fid]
    found = [f for f in after.findings if f.id == fid]
    problems = []
    if not found:
        problems.append(f"{fid} is not read")
    else:
        problems += [f"its {key} reads {getattr(found[0], key)!r}, not {value!r}" for key, value in expect.items() if getattr(found[0], key) != value]
    if others_after != others_before:
        problems.append("another finding reads differently")
    if len(after.problems) > len(before.problems):
        problems.append("the file has a new unreadable line")
    if problems:
        raise FindingError(f"{fid} would not read back as expected from {review.path} ({'; '.join(problems)}); it is left as it was")
    review.path.write_text(review.text, encoding="utf-8", newline="")  # each line keeps its own ending
    return found[0]


def _new_artifact(change: Change, artifact: CheckArtifact) -> str:
    """
    The check artifact's template with the change's name, its headings and guidance comments, without its example lines.
    """
    template = read_template(artifact.file).replace("<!-- change ref -->", change.name, 1)
    lines = template.splitlines(keepends=True)
    kept = [line for line, blanked in zip(lines, blank_comments(template).splitlines(), strict=True) if not LIST_ITEM_RE.match(blanked)]
    return re.sub(r"\n{3,}", "\n\n", "".join(kept))


# @req REQ-FLOW-016
def _suggestion(text: str, lang: str) -> list[str]:
    """
    The lines of a suggestion under a finding: the pinned ``**Suggestion**:`` line, then ``text`` unchanged in a fence
    indented by four spaces, marked ``lang``, longer than any run of backticks in it, so no line of it can close the
    fence (and, inside it, nothing routes the finding: REQ-FLOW-010). An empty ``text`` or a ``lang`` that is not one
    word raises ``FindingError``.
    """
    lines = text.rstrip("\r\n").splitlines()
    if not "".join(lines).strip():
        raise FindingError("the suggestion is empty")
    lang = lang.strip()
    if not re.fullmatch(r"[^\s`]+", lang):
        raise FindingError(f"the suggestion's language {lang!r} is not one word without backticks (diff, markdown, python, ...)")
    ticks = "`" * max(3, max((len(run) for run in re.findall(r"`+", text)), default=0) + 1)
    return ["  - **Suggestion**:", f"    {ticks}{lang}", *(f"    {line}" if line else "" for line in lines), f"    {ticks}"]


# @req REQ-FLOW-016
def add_finding(
    change: Change, kind: str, text: str, proposal: str, artifact: str = "review", check: str = "", suggestion: str | None = None, lang: str = "text"
) -> Finding:
    """
    Add an open finding of type ``kind`` (one of ``TYPE_PHASE``) to the check artifact ``artifact`` with its next free
    ID and its Proposal line (and a ``**Check**`` line when ``check`` is given) under ``## Findings``, creating the file
    from its template when missing; the finding as ``read_findings`` reads it after. An unknown ``artifact`` raises
    ``FindingError`` naming the check artifacts.

    A ``suggestion`` (multi-line text) goes after the Proposal line, as ``  - **Suggestion**:`` and the text in a fence
    indented by four spaces, marked ``lang``, of ``max(3, longest backtick run + 1)`` backticks; it never routes the
    finding. An empty ``suggestion`` raises ``FindingError``; ``None`` writes none.

    Implements REQ-FLOW-016.
    """
    target = _artifact(lambda: check_artifact(artifact))
    kind = kind.strip().lower()
    if kind not in TYPE_PHASE:
        raise FindingError(f"unknown finding type {kind!r}; one of {', '.join(TYPE_PHASE)}")
    text, proposal = _one_line(text, "finding's text"), _one_line(proposal, "proposal")
    check = " ".join(check.split())
    path, original = _open(change, target)
    review = _locate(path, original or _new_artifact(change, target), target)
    fid = f"{target.letter}{max((int(f.id[1:]) for f in parse_findings(review.text, target).findings), default=0) + 1}"
    fence = _suggestion(suggestion, lang) if suggestion is not None else []
    proposal_line = f"  - **Proposal**: {proposal}"
    new = [f"- [ ] {fid} **{kind}** {text}", *([f"  - **Check**: {check}"] if check else []), proposal_line, *fence]
    if review.section is None:
        _insert(review, len(review.lines), ["", "## Findings", "", *new])
    else:
        heading, end = review.section
        last = max((i for i in range(heading, end) if review.lines[i].strip()), default=heading)
        in_list = any(block.end == last for block in review.blocks.values())
        at = last + 1
        _insert(review, at, new + ([""] if at < len(review.lines) and review.lines[at].strip() else []))
        if not in_list:
            _insert(review, at, [""])
    # The step the reader gives: the form its Proposal line starts with, else its type; a form quoted in its text is text.
    phase, design_only = _route(proposal_line) or (TYPE_PHASE[kind], False)
    return _write(review, original, fid, {"done": False, "type": kind, "phase": phase, "design_only": design_only, "check": check})


# @req REQ-FLOW-016
def decide_finding(change: Change, finding_id: str, decision: str) -> Finding:
    """
    Write the finding's Decision (``back to <step>: ...``, ``back to design only: ...`` or ``accepted: ...``), replacing the one it has;
    ``accepted`` ticks it. The check artifact is the one the ID's letter names. The finding as ``read_findings`` reads it after.

    Implements REQ-FLOW-016.
    """
    decision = _one_line(decision, "decision")
    if not DECISION_RE.match(decision):
        raise FindingError(DECISION_FORM)
    target = _artifact(lambda: check_artifact_for(finding_id))
    path, original = _open(change, target)
    review = _locate(path, original, target)
    fid, block = _find(review, finding_id)
    current = next(f for f in parse_findings(original, target).findings if f.id == fid)
    line = f"{block.indent}  - **Decision**: {decision}"
    if fid in review.decisions:
        at = review.decisions[fid][0]  # only that line is replaced, keeping its own ending
        ending = review.lines[at][len(review.lines[at].rstrip("\r\n")) :]
        review.lines[at] = line + ending
    else:
        _insert(review, block.end + 1, [line])
    expect: dict[str, object]
    if decision.lower().startswith("accepted"):
        _tick(review, block)
        expect = {"done": True}
    else:
        step = _route(line)  # read as parse_findings reads the Decision line
        assert step is not None  # DECISION_RE checked the form
        phase, design_only = step
        expect = {"done": current.done, "phase": _next_step(current.done_in, design_only, target) if current.done_in else phase, "design_only": design_only}
    return _write(review, original, fid, expect)


# @req REQ-FLOW-016
def mark_finding_done(change: Change, finding_id: str, step: str, text: str) -> Finding:
    """
    Add ``done in <step>: <text>`` to the finding (``step``: specify, design, implement, test, code or review) in the
    check artifact its ID's letter names; the finding as ``read_findings`` reads it after.

    Implements REQ-FLOW-016.
    """
    step = step.strip().lower()
    if step not in NEXT_STEP:
        raise FindingError(f"unknown step {step!r}; one of {', '.join(NEXT_STEP)}")
    text = _one_line(text, "text")
    target = _artifact(lambda: check_artifact_for(finding_id))
    path, original = _open(change, target)
    review = _locate(path, original, target)
    fid, block = _find(review, finding_id)
    current = next(f for f in parse_findings(original, target).findings if f.id == fid)
    _insert(review, block.end + 1, [f"{block.indent}  - done in {step}: {text}"])
    return _write(review, original, fid, {"done": current.done, "done_in": step, "phase": _next_step(step, current.design_only, target)})


# @req REQ-FLOW-016
def close_finding(change: Change, finding_id: str, text: str) -> Finding:
    """
    Tick the finding and add ``confirmed in <artifact phase>: <text>`` in the check artifact its ID's letter names;
    the finding as ``read_findings`` reads it after.

    Implements REQ-FLOW-016.
    """
    text = _one_line(text, "text")
    target = _artifact(lambda: check_artifact_for(finding_id))
    path, original = _open(change, target)
    review = _locate(path, original, target)
    fid, block = _find(review, finding_id)
    _insert(review, block.end + 1, [f"{block.indent}  - confirmed in {review.artifact.phase}: {text}"])
    _tick(review, block)
    return _write(review, original, fid, {"done": True})
