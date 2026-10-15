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
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ..core.changes import Change
from ..core.errors import SpecworksError
from ..core.workspace import Workspace
from ..specs.specfile import H2_RE
from ..specs.trace import Analysis, scan_rule

CODE_EXTENSIONS = {
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".kts",
    ".scala", ".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".cs", ".fs", ".rb", ".php",
    ".swift", ".m", ".mm", ".dart", ".lua", ".ex", ".exs", ".erl", ".clj", ".sh", ".bash", ".ps1",
    ".sql", ".vue", ".svelte", ".zig", ".nim", ".r", ".jl",
}  # fmt: skip
BASE_CANDIDATES = ("origin/main", "main", "origin/master", "master")
REVIEW_FILE = "review.md"


class ReviewError(SpecworksError):
    """Raised when git cannot tell what changed."""


@dataclass
class ChangedFile:
    path: str  # relative to the workspace root
    kind: str  # "source", "test" or "other" (docs, config, data)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"path": self.path, "kind": self.kind, "tags": self.tags}


@dataclass
class ReviewReport:
    analysis: Analysis
    base: str | None = None
    changed: list[ChangedFile] | None = None  # None when git is not available
    note: str = ""

    @property
    def spec_errors(self) -> list[str]:
        return self.analysis.spec_errors

    @property
    def untraced_source(self) -> list[str]:
        return [f.path for f in self.changed or [] if f.kind == "source" and not any(t.startswith("REQ-") for t in f.tags)]

    @property
    def untraced_tests(self) -> list[str]:
        return [f.path for f in self.changed or [] if f.kind == "test" and not any(t.startswith("AC-") for t in f.tags)]

    def findings(self) -> dict[str, list[str]]:
        found = self.analysis.gaps
        return {
            "reqWithoutCode": found["reqWithoutCode"],
            "acWithoutTests": found["acWithoutTests"],
            "removedStillTagged": found["removedStillTagged"],
            "unknownTags": [t.at for t in self.analysis.unknown_tags],
            "untracedSource": self.untraced_source,
            "untracedTests": self.untraced_tests,
        }

    def to_dict(self) -> dict:
        found = self.findings()
        return {
            "base": self.base,
            "note": self.note,
            "specErrors": self.spec_errors,
            "findings": found,
            "findingCount": sum(len(v) for v in found.values()),
            "changedFiles": [f.to_dict() for f in self.changed] if self.changed is not None else None,
        }


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise ReviewError((proc.stderr or proc.stdout).strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def detect_base(cwd: Path) -> str:
    try:
        return _git(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip()
    except (ReviewError, OSError):
        pass
    for candidate in BASE_CANDIDATES:
        try:
            _git(cwd, "rev-parse", "--verify", "--quiet", candidate)
            return candidate
        except (ReviewError, OSError):
            continue
    raise ReviewError("cannot find the base branch; pass --base <branch>")


def changed_paths(ws: Workspace, base: str) -> list[str]:
    """Files changed since the merge base with ``base`` (committed, uncommitted, untracked), relative to the workspace."""
    git_root = Path(_git(ws.root, "rev-parse", "--show-toplevel").strip()).resolve()
    merge_base = _git(ws.root, "merge-base", base, "HEAD").strip()
    # -z: NUL-separated and never quoted, so names with non-ASCII characters or newlines come through as they are.
    names = set(_git(ws.root, "diff", "--name-only", "-z", merge_base).split("\0"))
    names |= set(_git(ws.root, "ls-files", "-z", "--others", "--exclude-standard", "--full-name").split("\0"))
    paths = []
    for name in sorted(n for n in names if n):
        path = (git_root / name).resolve()
        if path.is_file() and path.is_relative_to(ws.root):
            paths.append(ws.rel(path))
    return paths


def classify(ws: Workspace, rel: str) -> str | None:
    """``source``/``test``/``other``; None for files inside a workflow folder (specs, changes)."""
    path = ws.root / rel
    for module in ws.modules():
        if path.is_relative_to(module.root / module.config.dir):
            return None
    scanned, is_test = scan_rule(ws.owner(path), path)  # the module's test_globs / source_globs, as for tags
    if is_test:
        return "test"
    return "source" if scanned and path.suffix.lower() in CODE_EXTENSIONS else "other"


def review_change(analysis: Analysis, base: str | None = None) -> ReviewReport:
    """Drift candidates of the analysed change; changed files come from git against ``base``."""
    ws = analysis.ws
    report = ReviewReport(analysis)
    try:
        report.base = base or detect_base(ws.root)
        paths = changed_paths(ws, report.base)
    except (ReviewError, OSError) as exc:
        report.note = f"changed files unknown ({exc}); only spec -> code drift was checked"
        return report

    tags_by_file: dict[str, list[str]] = {}
    for tag in analysis.tags:
        tags_by_file.setdefault(tag.file, []).append(tag.id)
    report.changed = []
    for rel in paths:
        kind = classify(ws, rel)
        if kind is not None:
            report.changed.append(ChangedFile(path=rel, kind=kind, tags=sorted(set(tags_by_file.get(rel, [])))))
    return report


# --- review.md ----------------------------------------------------------------
#
# Findings are checkboxes (``- [ ] R<n> **<type>** ...``, ``- [x]`` once resolved);
# lines indented under one belong to it (its Decision). A Decision saying
# ``back to <phase>: <proposal>`` sends the finding to that phase; otherwise its
# type decides. A phase that carried out the proposal adds ``done in <phase>: <what
# changed>``: the finding stays open until review confirms it, but the work left is
# in the phases after that one. Untagged changed files are accounted for under their
# own heading.

# The phase that resolves each finding type, in workflow order (specify comes first).
TYPE_PHASE = {
    "spec-gap": "specify",
    "design-gap": "design",
    "test-gap": "test",
    "code-gap": "code",
    "tag": "code",
    "quality": "code",
}
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# A finding is a checkbox with its ID first: ``- [ ] R1 ...``; ``*``/``+``/``1.`` bullets
# and a bold ``**R1**`` are read too. Any other checkbox is reported, never skipped:
# a finding the parser cannot see would let the review gate pass with it open.
FINDING_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[(?P<mark>[ xX]?)\]\s+(?P<bold>\*\*)?(?P<id>R\d+)\b(?(bold)\*\*)(?P<text>.*)$")
CHECKBOX_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s*\[[^\]]?\]")
TYPE_RE = re.compile(r"\*\*([A-Za-z_-]+)\*\*")
BACK_RE = re.compile(r"\bback to (?P<phase>specify|design|test|code)\s*:", re.IGNORECASE)
DONE_RE = re.compile(r"\bdone in (?P<phase>specify|design|test|code)\s*:", re.IGNORECASE)
# Workflow order of the phases a finding can need, and the phase after each one.
FINDING_PHASES = ("specify", "design", "test", "code", "review")
ACCOUNTED_SECTION = "changed files without tags"


@dataclass
class Finding:
    id: str
    done: bool
    type: str  # "" when the finding names none
    text: str  # the finding's line, after its ID
    phase: str  # the phase that resolves it (after ``done_in``, the next one)
    routed: bool = True  # False: neither a known type nor a "back to"/"done in" phase, so ``phase`` is only a guess
    done_in: str = ""  # the phase that carried out its proposal (``done in <phase>:``), awaiting review

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


def parse_review(text: str) -> ReviewDoc:
    """Findings and the "Changed files without tags" section of review.md; HTML comments are ignored."""
    doc = ReviewDoc(exists=True)
    current: Finding | None = None
    section = ""
    accounted: list[str] = []
    # Comments are blanked line for line, so reported line numbers stay those of the file.
    uncommented = COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    for number, line in enumerate(uncommented.splitlines(), start=1):
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
        elif CHECKBOX_RE.match(line) and not line.startswith((" ", "\t")):  # indented ones belong to a finding
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
            finding.phase = FINDING_PHASES[FINDING_PHASES.index(finding.done_in) + 1]
        if not finding.done and not finding.routed:
            # The next build cycle starts from each open finding's phase, so it is never guessed.
            doc.problems.append(
                f"{finding.id}: type {finding.type or '(none)'!r} is not one of {', '.join(TYPE_PHASE)}; "
                f"name one, or add a Decision 'back to <specify|design|test|code>: ...'"
            )
    doc.accounted = "\n".join(accounted)
    return doc


def read_review(change: Change) -> ReviewDoc:
    path = change.path / REVIEW_FILE
    return parse_review(path.read_text(encoding="utf-8")) if path.is_file() else ReviewDoc(exists=False)
