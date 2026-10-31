"""Drift between a change's specs and its code, as far as the CLI can see it.

Two directions:

- spec -> code: requirements without ``@req`` code, criteria without ``@ac``
  tests, removed requirements still tagged, tags to unknown IDs;
- code -> spec: files changed on the branch (git diff against the base branch,
  plus uncommitted and untracked files) whose code carries no ``@req`` tag, or
  whose tests carry no ``@ac`` tag - behaviour or tests no requirement explains.

These are candidates, not verdicts: the review skill reads the code and decides
with the user whether the code or the spec is right.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..core.changes import META_FILE, Change
from ..core.errors import SpecworksError
from ..core.files import read_text
from ..core.git import GitError, git, git_text
from ..core.workspace import Workspace
from ..specs.specfile import H2_RE, blank_comments, fenced
from ..specs.trace import Analysis, scan_rule
from .artifacts import read_template

CODE_EXTENSIONS = {
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".kts",
    ".scala", ".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".cs", ".fs", ".rb", ".php",
    ".swift", ".m", ".mm", ".dart", ".lua", ".ex", ".exs", ".erl", ".clj", ".sh", ".bash", ".ps1",
    ".sql", ".vue", ".svelte", ".zig", ".nim", ".r", ".jl",
}  # fmt: skip
BASE_CANDIDATES = ("origin/main", "main", "origin/master", "master")
REVIEW_FILE = "review.md"


@dataclass
class ChangedFile:
    path: str  # relative to the workspace root
    kind: str  # "source", "test", "other" (docs, config, data) or "deleted"
    tags: list[str] = field(default_factory=list)
    was: str = ""  # for a deleted file, the kind it had

    def to_dict(self) -> dict:
        return {"path": self.path, "kind": self.kind, "tags": self.tags} | ({"was": self.was} if self.was else {})


@dataclass
class ReviewReport:
    analysis: Analysis
    base: str | None = None
    changed: list[ChangedFile] | None = None  # None when git is not available
    note: str = ""
    since: str = ""  # what the changed files are compared with: the base, or where the change started when HEAD is on the base
    on_base: bool = False  # HEAD is on the base branch and the change has no commit to start from

    @property
    def spec_errors(self) -> list[str]:
        return self.analysis.spec_errors

    @property
    def untraced_source(self) -> list[str]:
        return [f.path for f in self.changed or [] if f.kind == "source" and not any(t.startswith("REQ-") for t in f.tags)]

    @property
    def untraced_tests(self) -> list[str]:
        return [f.path for f in self.changed or [] if f.kind == "test" and not any(t.startswith("AC-") for t in f.tags)]

    @property
    def deleted_files(self) -> list[str]:
        """Source and test files deleted on the branch: deleted code is reviewed like changed code."""
        return [f.path for f in self.changed or [] if f.kind == "deleted" and f.was in ("source", "test")]

    def findings(self) -> dict[str, list[str]]:
        found = self.analysis.gaps
        return {
            "reqWithoutCode": found["reqWithoutCode"],
            "acWithoutTests": found["acWithoutTests"],
            "removedStillTagged": found["removedStillTagged"],
            "unknownTags": [t.at for t in self.analysis.unknown_tags],
            "untracedSource": self.untraced_source,
            "untracedTests": self.untraced_tests,
            "deletedFiles": self.deleted_files,
        }

    def to_dict(self) -> dict:
        found = self.findings()
        return {
            "base": self.base,
            "since": self.since,
            "note": self.note,
            "specErrors": self.spec_errors,
            "findings": found,
            "findingCount": sum(len(v) for v in found.values()),
            "changedFiles": [f.to_dict() for f in self.changed] if self.changed is not None else None,
        }


# @req REQ-FLOW-009
def detect_base(cwd: Path) -> str:
    try:
        return git_text(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip()
    except GitError:
        pass
    for candidate in BASE_CANDIDATES:
        try:
            git(cwd, "rev-parse", "--verify", "--quiet", candidate)
            return candidate
        except GitError:
            continue
    raise GitError("cannot find the base branch; pass --base <branch>")


# @req REQ-FLOW-009
def change_start(ws: Workspace, change: Change) -> str | None:
    """The parent of the newest commit that added the change's metadata (an archived change may have had its name), if any."""
    meta = (change.path / META_FILE).relative_to(ws.root).as_posix()
    added = git_text(ws.root, "log", "--diff-filter=A", "--format=%H", "-1", "--", meta).strip()
    if not added:
        return None
    try:
        return git_text(ws.root, "rev-parse", "--verify", "--quiet", f"{added}^").strip()
    except GitError:
        return None  # added in the first commit: there is nothing before it


# @req REQ-FLOW-009
def _changed_names(ws: Workspace, since: str) -> list[Path]:
    """Every path git reports as changed since the commit ``since`` (committed, uncommitted, untracked), resolved."""
    git_root = Path(git_text(ws.root, "rev-parse", "--show-toplevel").strip()).resolve()
    # -z: NUL-separated and never quoted, so names with non-ASCII characters or newlines come through as they are.
    names = set(git_text(ws.root, "diff", "--name-only", "-z", since).split("\0"))
    names |= set(git_text(ws.root, "ls-files", "-z", "--others", "--exclude-standard", "--full-name").split("\0"))
    return [(git_root / name).resolve() for name in sorted(n for n in names if n)]


def changed_paths(ws: Workspace, since: str) -> list[str]:
    """Files changed since the commit ``since`` (committed, uncommitted, untracked), relative to the workspace."""
    return [ws.rel(path) for path in _changed_names(ws, since) if path.is_file() and path.is_relative_to(ws.root)]


# @req REQ-FLOW-009
def deleted_paths(ws: Workspace, since: str) -> list[str]:
    """Files changed since the commit ``since`` that no longer exist, relative to the workspace."""
    return [ws.rel(path) for path in _changed_names(ws, since) if not path.exists() and path.is_relative_to(ws.root)]


def changed_file_kind(ws: Workspace, rel: str) -> str | None:
    """The ``ChangedFile.kind`` of a changed file (``source``, ``test`` or ``other``); None inside a workflow folder (specs, changes)."""
    path = ws.root / rel
    for module in ws.modules():
        if path.is_relative_to(module.root / module.config.dir):
            return None
    scanned, is_test = scan_rule(ws.owner(path), path)  # the module's test_globs / source_globs, as for tags
    if is_test:
        return "test"
    return "source" if scanned and path.suffix.lower() in CODE_EXTENSIONS else "other"


# @req REQ-FLOW-009
def review_change(analysis: Analysis, base: str | None = None) -> ReviewReport:
    """Drift candidates of the analysed change; changed files come from git against ``base``."""
    ws = analysis.ws
    report = ReviewReport(analysis)
    try:
        report.base = base or detect_base(ws.root)
        since = git_text(ws.root, "merge-base", report.base, "HEAD").strip()
        report.since = report.base
        # On the base branch itself the merge base is HEAD, which would hide every commit of the change.
        if since == git_text(ws.root, "rev-parse", "HEAD").strip():
            if start := change_start(ws, analysis.change):
                since, report.since = start, f"{report.base} at the commit before {analysis.change.name} started, {start[:7]}"
            else:
                report.on_base = True
                report.note = (
                    f"HEAD is on {report.base} and no earlier commit marks where {analysis.change.name} started, so only "
                    "uncommitted files are compared; work on a branch, or pass --base <the commit before the change started>"
                )
        paths, deleted = changed_paths(ws, since), deleted_paths(ws, since)
    except (GitError, OSError) as exc:
        report.note = f"changed files unknown ({exc}); only spec -> code drift was checked"
        return report

    tags_by_file: dict[str, list[str]] = {}
    for tag in analysis.tags:
        tags_by_file.setdefault(tag.file, []).append(tag.id)
    report.changed = []
    for rel in paths:
        kind = changed_file_kind(ws, rel)
        if kind is not None:
            report.changed.append(ChangedFile(path=rel, kind=kind, tags=sorted(set(tags_by_file.get(rel, [])))))
    for rel in deleted:  # what each one was decides whether it must be accounted for in review.md
        if (was := changed_file_kind(ws, rel)) is not None:
            report.changed.append(ChangedFile(path=rel, kind="deleted", was=was))
    return report


# --- review.md ----------------------------------------------------------------
#
# Findings are checkboxes (``- [ ] R<n> **<type>** ...``, ``- [x]`` once resolved);
# lines indented under one belong to it (its Decision). A Decision saying
# ``back to <step>: <proposal>`` sends the finding to that step (specify, design,
# implement, test or code); otherwise its type decides. A step that carried out the
# proposal adds ``done in <step>: <what changed>``: the finding stays open until
# review confirms it, but the work left is in the steps after that one. Untagged
# changed files are accounted for under their own heading.

# The step that resolves each finding type, in workflow order (specify comes first).
TYPE_PHASE = {
    "spec-gap": "specify",
    "design-gap": "design",
    "test-gap": "test",
    "code-gap": "code",
    "tag": "code",
    "quality": "code",
}
# A finding is a checkbox with its ID first: ``- [ ] R1 ...``; ``*``/``+``/``1.`` bullets
# and a bold ``**R1**`` are read too. Any other checkbox is reported, never skipped:
# a finding the parser cannot see would let the review gate pass with it open.
FINDING_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[(?P<mark>[ xX]?)\]\s+(?P<bold>\*\*)?(?P<id>R\d+)\b(?(bold)\*\*)(?P<text>.*)$")
CHECKBOX_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s*\[[^\]]?\]")
TYPE_RE = re.compile(r"\*\*([A-Za-z_-]+)\*\*")
BACK_RE = re.compile(r"\bback to (?P<phase>specify|design|implement|test|code)\s*:", re.IGNORECASE)
DONE_RE = re.compile(r"\bdone in (?P<phase>specify|design|implement|test|code)\s*:", re.IGNORECASE)
# The steps a finding can be routed to, in workflow order: implement is both halves, test and code one each.
FINDING_STEPS = ("specify", "design", "implement", "test", "code", "review")
# The step a finding needs once a step carried out its proposal (``done in <step>:``).
NEXT_STEP = {"specify": "design", "design": "implement", "implement": "review", "test": "review", "code": "review"}
ACCOUNTED_SECTION = "changed files without tags"


@dataclass
class Finding:
    id: str
    done: bool
    type: str  # "" when the finding names none
    text: str  # the finding's line, after its ID
    phase: str  # the step that resolves it, one of FINDING_STEPS (after ``done_in``, the next one)
    routed: bool = True  # False: neither a known type nor a "back to"/"done in" step, so ``phase`` is only a guess
    done_in: str = ""  # the step that carried out its proposal (``done in <step>:``), awaiting review

    def to_dict(self) -> dict:
        data = {"id": self.id, "type": self.type, "text": self.text, "phase": self.phase}
        if self.done_in:
            data["doneIn"] = self.done_in
        return data


@dataclass
class ReviewDoc:
    exists: bool
    findings: list[Finding] = field(default_factory=list)
    accounted: str = ""  # text of "## Changed files without tags"
    problems: list[str] = field(default_factory=list)  # checkbox lines that are not readable findings

    @property
    def open(self) -> list[Finding]:
        return [f for f in self.findings if not f.done]

    def accounts_for(self, path: str) -> bool:
        """``path`` appears as a whole path under "Changed files without tags" (``src/a.py``, not ``src/a.py.bak``)."""
        return re.search(rf"(?<![\w./-]){re.escape(path)}(?![\w./-])", self.accounted) is not None


# @req REQ-FLOW-010
def parse_review(text: str) -> ReviewDoc:
    """Findings and the "Changed files without tags" section of review.md; HTML comments and code fences are ignored."""
    doc = ReviewDoc(exists=True)
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
        if match := FINDING_RE.match(line):
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
        elif CHECKBOX_RE.match(line) and (current is None or not line.startswith((" ", "\t"))):
            # Indented under a finding, it is part of that finding (a sub-step); anywhere else it could hide open work.
            doc.problems.append(f"line {number}: {line.strip()!r} is not a finding; write it as '- [ ] R<n> **<type>** ...'")
            current = None
        elif current is not None and line.strip() and not line.startswith((" ", "\t")):
            current = None  # back at the top level: the finding's block has ended
        if current is not None and (back := BACK_RE.search(line)):
            current.phase, current.routed = back.group("phase").lower(), True
        if current is not None and (carried := DONE_RE.search(line)):
            current.done_in, current.routed = carried.group("phase").lower(), True
    for finding in doc.findings:
        if finding.done_in:
            finding.phase = NEXT_STEP[finding.done_in]
        if not finding.done and not finding.routed:
            # The next build cycle starts from each open finding's phase, so it is never guessed.
            doc.problems.append(
                f"{finding.id}: type {finding.type or '(none)'!r} is not one of {', '.join(TYPE_PHASE)}; "
                f"name one, or add a Decision 'back to <specify|design|implement|test|code>: ...'"
            )
    doc.accounted = "\n".join(accounted)
    return doc


def read_review(change: Change) -> ReviewDoc:
    path = change.path / REVIEW_FILE
    return parse_review(read_text(path)) if path.is_file() else ReviewDoc(exists=False)


# --- writing review.md --------------------------------------------------------
#
# Each writer edits review.md's text in place (one line added at the end of the
# finding's block, a Decision replaced, a box ticked), reads the edited text back
# with ``parse_review``, and writes the file only when the finding reads as expected.



# A Decision line under a finding, as written by hand (``- **Decision**: ...``) or by ``decide_finding``.
DECISION_LINE_RE = re.compile(r"^(?P<indent>\s*)(?:[-*+]|\d+[.)])\s+\**Decision\**\s*:", re.IGNORECASE)
DECISION_RE = re.compile(r"^(?:back to (?:specify|design|implement|test|code)|accepted)\s*:\s*\S", re.IGNORECASE)
DECISION_FORM = "a decision starts with 'back to <step>:' (specify, design, implement, test or code) or 'accepted:'"
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
CHECKBOX_MARK_RE = re.compile(r"\[[ xX]?\]")


class FindingError(SpecworksError):
    """A refused write to review.md: an unknown finding, type or step, an empty text, a decision in another form,
    or an edit that does not read back; review.md is left as it was."""


@dataclass
class _Block:
    start: int  # the finding's checkbox line
    end: int  # its last non-blank line
    indent: str  # the checkbox line's own indentation


@dataclass
class _Review:
    """review.md split into lines (each with its own ending), where its findings and the Findings section are."""

    path: Path
    lines: list[str]
    newline: str
    blocks: dict[str, _Block] = field(default_factory=dict)
    section: tuple[int, int] | None = None  # the "## Findings" heading and the line after its last one
    decisions: dict[str, list[int]] = field(default_factory=dict)  # the Decision lines under each finding

    @property
    def text(self) -> str:
        return "".join(self.lines)


# @req REQ-FLOW-016
def _locate(path: Path, text: str) -> _Review:
    """Where each finding's block is, read the way ``parse_review`` reads it (comments blanked, fences ignored)."""
    review = _Review(path, text.splitlines(keepends=True), "\r\n" if "\r\n" in text else "\n")
    lines = blank_comments(text).splitlines()
    current: _Block | None = None
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
        if match := FINDING_RE.match(line):
            current = _Block(number, number, line[: len(line) - len(line.lstrip())])
            review.blocks.setdefault(match.group("id"), current)  # a repeated ID: the first one is the finding
            continue
        if (CHECKBOX_RE.match(line) and (current is None or not indented)) or (current is not None and line.strip() and not indented):
            current = None
        if current is not None and line.strip():
            current.end = number
            if DECISION_LINE_RE.match(line):
                review.decisions.setdefault(next(k for k, b in review.blocks.items() if b is current), []).append(number)
    return review


def _one_line(value: str, what: str) -> str:
    text = " ".join(value.split())
    if not text:
        raise FindingError(f"the {what} is empty")
    return text


def _open(change: Change) -> tuple[Path, str]:
    path = change.path / REVIEW_FILE
    return path, read_text(path, keep_newlines=True) if path.is_file() else ""


def _find(review: _Review, finding_id: str) -> tuple[str, _Block]:
    fid = finding_id.strip().upper()
    if fid not in review.blocks:
        raise FindingError(f"no finding {finding_id.strip()} in {review.path}")
    return fid, review.blocks[fid]


def _insert(review: _Review, at: int, new: list[str]) -> None:
    """Insert ``new`` lines before line ``at``, each ending with the file's own newline."""
    if at > 0 and not review.lines[at - 1].endswith(("\n", "\r")):
        review.lines[at - 1] += review.newline
    review.lines[at:at] = [line + review.newline for line in new]


def _tick(review: _Review, block: _Block) -> None:
    review.lines[block.start] = CHECKBOX_MARK_RE.sub("[x]", review.lines[block.start], count=1)


def _write(review: _Review, original: str, fid: str, expect: dict[str, object]) -> Finding:
    """Write the edited review.md only when ``fid`` reads back as ``expect`` and every other finding as before."""
    before, after = parse_review(original) if original else ReviewDoc(exists=False), parse_review(review.text)
    others_before = [(f.id, f.done, f.type, f.text, f.phase, f.done_in) for f in before.findings if f.id != fid]
    others_after = [(f.id, f.done, f.type, f.text, f.phase, f.done_in) for f in after.findings if f.id != fid]
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


def _new_review(change: Change) -> str:
    """The review.md template with the change's name, its headings and guidance comments, without its example lines."""
    template = read_template(REVIEW_FILE).replace("<!-- change ref -->", change.name, 1)
    lines = template.splitlines(keepends=True)
    kept = [line for line, blanked in zip(lines, blank_comments(template).splitlines(), strict=True) if not LIST_ITEM_RE.match(blanked)]
    return re.sub(r"\n{3,}", "\n\n", "".join(kept))


# @req REQ-FLOW-016
def add_finding(change: Change, kind: str, text: str, proposal: str) -> Finding:
    """Add an open finding of type ``kind`` (one of ``TYPE_PHASE``) with the next free ID and its Proposal line under
    ``## Findings``, creating review.md from its template when missing; the finding as ``read_review`` reads it after.

    Implements REQ-FLOW-016.
    """
    kind = kind.strip().lower()
    if kind not in TYPE_PHASE:
        raise FindingError(f"unknown finding type {kind!r}; one of {', '.join(TYPE_PHASE)}")
    text, proposal = _one_line(text, "finding's text"), _one_line(proposal, "proposal")
    path, original = _open(change)
    review = _locate(path, original or _new_review(change))
    fid = f"R{max((int(f.id[1:]) for f in parse_review(review.text).findings), default=0) + 1}"
    new = [f"- [ ] {fid} **{kind}** {text}", f"  - **Proposal**: {proposal}"]
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
    return _write(review, original, fid, {"done": False, "type": kind, "phase": TYPE_PHASE[kind]})


# @req REQ-FLOW-016
def decide_finding(change: Change, finding_id: str, decision: str) -> Finding:
    """Write the finding's Decision (``back to <step>: ...`` or ``accepted: ...``), replacing the one it has;
    ``accepted`` ticks it. The finding as ``read_review`` reads it after.

    Implements REQ-FLOW-016.
    """
    decision = _one_line(decision, "decision")
    if not DECISION_RE.match(decision):
        raise FindingError(DECISION_FORM)
    path, original = _open(change)
    review = _locate(path, original)
    fid, block = _find(review, finding_id)
    current = next(f for f in parse_review(original).findings if f.id == fid)
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
        step = BACK_RE.match(decision)
        assert step is not None  # DECISION_RE checked the form
        expect = {"done": current.done, "phase": NEXT_STEP[current.done_in] if current.done_in else step.group("phase").lower()}
    return _write(review, original, fid, expect)


# @req REQ-FLOW-016
def mark_finding_done(change: Change, finding_id: str, step: str, text: str) -> Finding:
    """Add ``done in <step>: <text>`` to the finding (``step``: specify, design, implement, test or code);
    the finding as ``read_review`` reads it after.

    Implements REQ-FLOW-016.
    """
    step = step.strip().lower()
    if step not in NEXT_STEP:
        raise FindingError(f"unknown step {step!r}; one of {', '.join(NEXT_STEP)}")
    text = _one_line(text, "text")
    path, original = _open(change)
    review = _locate(path, original)
    fid, block = _find(review, finding_id)
    current = next(f for f in parse_review(original).findings if f.id == fid)
    _insert(review, block.end + 1, [f"{block.indent}  - done in {step}: {text}"])
    return _write(review, original, fid, {"done": current.done, "done_in": step, "phase": NEXT_STEP[step]})


# @req REQ-FLOW-016
def close_finding(change: Change, finding_id: str, text: str) -> Finding:
    """Tick the finding and add ``confirmed in review: <text>``; the finding as ``read_review`` reads it after.

    Implements REQ-FLOW-016.
    """
    text = _one_line(text, "text")
    path, original = _open(change)
    review = _locate(path, original)
    fid, block = _find(review, finding_id)
    _insert(review, block.end + 1, [f"{block.indent}  - confirmed in review: {text}"])
    _tick(review, block)
    return _write(review, original, fid, {"done": True})
