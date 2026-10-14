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

from .changes import Change
from .trace import Tag, build_matrix, gaps, is_test_file, scan_tags, unknown_tags
from .validate import ChangeSpecs, validate_change
from .workspace import Workspace

CODE_EXTENSIONS = {
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".kts",
    ".scala", ".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".cs", ".fs", ".rb", ".php",
    ".swift", ".m", ".mm", ".dart", ".lua", ".ex", ".exs", ".erl", ".clj", ".sh", ".bash", ".ps1",
    ".sql", ".vue", ".svelte", ".zig", ".nim", ".r", ".jl",
}  # fmt: skip
BASE_CANDIDATES = ("origin/main", "main", "origin/master", "master")


class ReviewError(Exception):
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
    base: str | None
    changed: list[ChangedFile] | None  # None when git is not available
    gaps: dict[str, list[str]]
    unknown_tags: list[Tag]
    spec_errors: list[str]
    note: str = ""

    @property
    def untraced_source(self) -> list[str]:
        return [f.path for f in self.changed or [] if f.kind == "source" and not any(t.startswith("REQ-") for t in f.tags)]

    @property
    def untraced_tests(self) -> list[str]:
        return [f.path for f in self.changed or [] if f.kind == "test" and not any(t.startswith("AC-") for t in f.tags)]

    def findings(self) -> dict[str, list[str]]:
        return {
            "reqWithoutCode": self.gaps["reqWithoutCode"],
            "acWithoutTests": self.gaps["acWithoutTests"],
            "removedStillTagged": self.gaps["removedStillTagged"],
            "unknownTags": [f"{t.id} at {t.where}" for t in self.unknown_tags],
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
    names = set(_git(ws.root, "diff", "--name-only", merge_base).splitlines())
    names |= set(_git(ws.root, "ls-files", "--others", "--exclude-standard", "--full-name").splitlines())
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
    test_globs = [g for m in ws.modules() for g in m.config.test_globs]
    if is_test_file(rel, test_globs):
        return "test"
    return "source" if path.suffix.lower() in CODE_EXTENSIONS else "other"


def review_change(ws: Workspace, change: Change, base: str | None = None) -> tuple[ChangeSpecs, ReviewReport]:
    specs, issues = validate_change(ws, change)
    tags = scan_tags(ws)
    found = gaps(build_matrix(specs, tags))
    report = ReviewReport(
        base=None,
        changed=None,
        gaps=found,
        unknown_tags=unknown_tags(specs, tags),
        spec_errors=[str(i) for i in issues if i.level == "error"],
    )
    try:
        report.base = base or detect_base(ws.root)
        paths = changed_paths(ws, report.base)
    except (ReviewError, OSError) as exc:
        report.note = f"changed files unknown ({exc}); only spec -> code drift was checked"
        return specs, report

    tags_by_file: dict[str, list[str]] = {}
    for tag in tags:
        tags_by_file.setdefault(tag.file, []).append(tag.id)
    report.changed = []
    for rel in paths:
        kind = classify(ws, rel)
        if kind is not None:
            report.changed.append(ChangedFile(path=rel, kind=kind, tags=sorted(set(tags_by_file.get(rel, [])))))
    return specs, report


REVIEW_FILE = "review.md"


OPEN_FINDING_RE = re.compile(r"(?m)^\s*- \[\s*\]\s+(R\d+\b.*)$")


def review_findings(change: Change) -> tuple[bool, list[str], str]:
    """(review.md exists, open findings, review.md text); findings are '- [ ] R<n> ...' checkboxes."""
    path = change.path / REVIEW_FILE
    if not path.is_file():
        return False, [], ""
    text = path.read_text(encoding="utf-8")
    return True, [m.group(1).strip() for m in OPEN_FINDING_RE.finditer(text)], text
