"""Traceability: requirement -> acceptance criteria -> tasks -> tests -> code.

Tests and code link back to the specs with comment tags, in any language::

    # @ac AC-AUTH-001.1        (in a test)
    // @req REQ-AUTH-001       (in code)

Each file follows the config of the module that owns it (the nearest one), with
globs relative to that module's folder. A file counts as a test when it matches
the module's ``test_globs`` or, when none are set, when its name or folder looks
like a test (``test_x.py``, ``x_test.go``, ``x.test.ts``, ``x.spec.js``,
``x_spec.rb``, ``tests/``, ``__tests__/``...). ``source_globs``, when set, limit
the other files scanned; tests are always scanned.
"""

from __future__ import annotations

import fnmatch
import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from ..core.changes import Change
from ..core.workspace import Workspace
from .check import ChangeSpecs, Issue, check_change
from .specfile import id_prefix

TAG_RE = re.compile(r"@(?P<kind>req|ac)\s+(?P<id>(?:REQ|AC)-[A-Z0-9][A-Z0-9.-]*[A-Z0-9])")
SKIP_DIRS = {"node_modules", "__pycache__", "venv", "dist", "build", "target", "out", "vendor", "site-packages"}
# Not "spec"/"specs": they often hold source (spec parsers, OpenAPI specs); RSpec files
# are still found by name (``*_spec.rb``).
TEST_DIRS = {"test", "tests", "__tests__", "testing"}
TEST_NAME_RE = re.compile(r"(^test_|_test\.|\.test\.|\.spec\.|Test\.|Tests\.|_spec\.)")
MAX_FILE_BYTES = 1_000_000


@dataclass
class Tag:
    id: str
    kind: str  # "req" or "ac"
    file: str
    line: int
    is_test: bool

    @property
    def where(self) -> str:
        return f"{self.file}:{self.line}"

    @property
    def at(self) -> str:
        return f"{self.id} at {self.where}"


@dataclass
class Row:
    capability: str
    req: str
    title: str
    section: str
    ac: str | None = None
    ac_title: str = ""
    tasks: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    code: list[str] = field(default_factory=list)


def is_test_file(rel: str, test_globs: list[str]) -> bool:
    if test_globs:
        return any(fnmatch.fnmatch(rel, g) for g in test_globs)
    parts = rel.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME_RE.search(parts[-1]))


def file_classifier(ws: Workspace) -> Callable[[Path], tuple[bool, bool]]:
    """``classify(path) -> (scanned, is_test)`` for files of the workspace, by the config of the module owning each one."""
    deepest_first = sorted(ws.modules(), key=lambda m: len(m.root.parts), reverse=True)

    def classify(path: Path) -> tuple[bool, bool]:
        module = next(m for m in deepest_first if path.is_relative_to(m.root))
        rel = path.relative_to(module.root).as_posix()
        cfg = module.config
        is_test = is_test_file(rel, cfg.test_globs)
        return is_test or not cfg.source_globs or any(fnmatch.fnmatch(rel, g) for g in cfg.source_globs), is_test

    return classify


def scan_tags(ws: Workspace) -> list[Tag]:
    """Every @req / @ac tag in the workspace, skipping hidden, vendored and workflow folders."""
    skip_roots = {(m.root / m.config.dir).resolve() for m in ws.modules()}
    classify = file_classifier(ws)
    tags: list[Tag] = []
    for dirpath, dirnames, filenames in os.walk(ws.root):
        here = Path(dirpath)
        dirnames[:] = sorted(
            d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS and (here / d).resolve() not in skip_roots
        )
        for name in sorted(filenames):
            path = here / name
            scanned, is_test = classify(path)
            if not scanned:
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "@req" not in text and "@ac" not in text:
                continue
            rel = ws.rel(path)
            for number, line in enumerate(text.splitlines(), start=1):
                for match in TAG_RE.finditer(line):
                    tags.append(Tag(id=match.group("id"), kind=match.group("kind"), file=rel, line=number, is_test=is_test))
    return tags


def build_matrix(specs: ChangeSpecs, tags: list[Tag]) -> list[Row]:
    tasks_by_id: dict[str, list[str]] = {}
    for task in specs.tasks:
        for ref in task.ids:
            tasks_by_id.setdefault(ref, []).append(task.num)
    tests_by_id: dict[str, list[str]] = {}
    code_by_id: dict[str, list[str]] = {}
    for tag in tags:
        (tests_by_id if tag.is_test else code_by_id).setdefault(tag.id, []).append(tag.where)

    rows: list[Row] = []
    for delta, req in specs.requirements():
        req_id = req.id or "?"
        base = dict(capability=delta.cap.ref, req=req_id, title=req.title, section=req.section)
        req_tasks = tasks_by_id.get(req_id, [])
        code = code_by_id.get(req_id, [])
        if req.section == "REMOVED" or not req.scenarios:
            rows.append(Row(**base, tasks=req_tasks, tests=tests_by_id.get(req_id, []), code=code))
            continue
        for sc in req.scenarios:
            ac_id = sc.id or "?"
            rows.append(
                Row(
                    **base,
                    ac=sc.id,
                    ac_title=sc.title,
                    tasks=sorted(set(req_tasks + tasks_by_id.get(ac_id, [])), key=_task_key),
                    tests=tests_by_id.get(ac_id, []),
                    code=code,
                )
            )
    return rows


def _task_key(num: str) -> tuple[int, ...]:
    return tuple(int(p) for p in num.split("."))


def gaps(rows: list[Row]) -> dict[str, list[str]]:
    active = [r for r in rows if r.section != "REMOVED"]
    return {
        "acWithoutTasks": [r.ac for r in active if r.ac and not r.tasks],
        "acWithoutTests": [r.ac for r in active if r.ac and not r.tests],
        "reqWithoutCode": sorted({r.req for r in active if not r.code}),
        "removedStillTagged": sorted({r.req for r in rows if r.section == "REMOVED" and (r.tests or r.code)}),
    }


def unknown_tags(specs: ChangeSpecs, tags: list[Tag]) -> list[Tag]:
    """Tags whose ID belongs to a capability this change touches but is in neither the delta nor the living spec."""
    prefixes = {d.cap.prefix for d in specs.deltas}
    known = specs.known_ids()
    return [t for t in tags if t.id not in known and id_prefix(t.id) in prefixes]


def to_markdown(change_ref: str, rows: list[Row], found: dict[str, list[str]]) -> str:
    def cell(items: list[str]) -> str:
        return "<br>".join(f"`{i}`" for i in items) if items else "—"

    out = [
        f"# Traceability: {change_ref}",
        "",
        "Generated by `specworks trace --write`; do not edit by hand.",
        "",
        "| Capability | Requirement | Acceptance criterion | Tasks | Tests | Code |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        if r.section == "REMOVED":
            continue
        ac = f"{r.ac} {r.ac_title}".strip() if r.ac else "—"
        out.append(
            f"| {r.capability} | {r.req} {r.title} ({r.section}) | {ac} | {', '.join(r.tasks) or '—'} | {cell(r.tests)} | {cell(r.code)} |"
        )
    removed = [r for r in rows if r.section == "REMOVED"]
    if removed:
        out += ["", "## Removed", "", "| Capability | Requirement | Tasks | Still tagged in |", "|---|---|---|---|"]
        out += [f"| {r.capability} | {r.req} {r.title} | {', '.join(r.tasks) or '—'} | {cell(r.tests + r.code)} |" for r in removed]
    labels = {
        "acWithoutTasks": "Acceptance criteria without a task",
        "acWithoutTests": "Acceptance criteria without a test (`@ac`)",
        "reqWithoutCode": "Requirements without code (`@req`)",
        "removedStillTagged": "Removed requirements still tagged in tests or code",
    }
    out += ["", "## Gaps", ""]
    out += [f"- {labels[k]}: {', '.join(v)}" for k, v in found.items() if v] or ["- None"]
    return "\n".join(out) + "\n"


def write_traceability(change: Change, text: str) -> Path:
    path = change.path / "traceability.md"
    path.write_text(text, encoding="utf-8")
    return path


class Analysis:
    """What the CLI knows about a change: its parsed specs and their issues, the workspace's tags and the gaps.

    Each part is computed on first use, so a caller that needs only the specs never scans the workspace.
    """

    def __init__(self, ws: Workspace, change: Change) -> None:
        self.ws, self.change = ws, change

    @cached_property
    def _checked(self) -> tuple[ChangeSpecs, list[Issue]]:
        return check_change(self.ws, self.change)

    @property
    def specs(self) -> ChangeSpecs:
        return self._checked[0]

    @property
    def issues(self) -> list[Issue]:
        return self._checked[1]

    @property
    def spec_errors(self) -> list[str]:
        return [str(i) for i in self.issues if i.level == "error"]

    @cached_property
    def tags(self) -> list[Tag]:
        return scan_tags(self.ws)

    @cached_property
    def rows(self) -> list[Row]:
        return build_matrix(self.specs, self.tags)

    @cached_property
    def gaps(self) -> dict[str, list[str]]:
        return gaps(self.rows)

    @property
    def acs_without_tasks(self) -> list[str]:
        """Needs no tag scan: tasks come from tasks.md."""
        return gaps(build_matrix(self.specs, []))["acWithoutTasks"]

    @cached_property
    def unknown_tags(self) -> list[Tag]:
        return unknown_tags(self.specs, self.tags)
