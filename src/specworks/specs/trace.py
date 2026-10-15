"""Traceability: requirement -> acceptance criteria -> tasks -> tests -> code.

Tests and code link back to the specs with comment tags, in any language::

    # @ac AC-AUTH-001.1        (in a test)
    // @req REQ-AUTH-001       (in code)

Each file belongs to the innermost module whose folder holds it, and that
module's ``source_globs`` / ``test_globs`` (relative to its folder) decide
whether it is scanned and whether it is a test. A file counts as a test when
it matches the module's ``test_globs`` or, when none are set, when its name or
folder looks like a test (``test_x.py``, ``x_test.go``, ``x.test.ts``,
``x.spec.js``, ``x_spec.rb``, ``tests/``, ``__tests__/``...).
"""

from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..core.changes import Change
from ..core.workspace import Module, Workspace
from .check import ChangeSpecs
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


def is_test_path(module: Module, path: Path) -> bool:
    """Whether ``path`` (a file of ``module``) is a test, by the module's ``test_globs`` relative to its folder."""
    return is_test_file(path.relative_to(module.root).as_posix(), module.config.test_globs)


def scan_tags(ws: Workspace) -> list[Tag]:
    """Every @req / @ac tag in the workspace, skipping hidden, vendored and workflow folders."""
    skip_roots = {(m.root / m.config.dir).resolve() for m in ws.modules()}
    tags: list[Tag] = []
    for dirpath, dirnames, filenames in os.walk(ws.root):
        here = Path(dirpath)
        dirnames[:] = sorted(
            d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS and (here / d).resolve() not in skip_roots
        )
        module = ws.owner(here)
        globs = module.config.source_globs + module.config.test_globs
        for name in sorted(filenames):
            path = here / name
            rel = ws.rel(path)
            if globs and not any(fnmatch.fnmatch(path.relative_to(module.root).as_posix(), g) for g in globs):
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "@req" not in text and "@ac" not in text:
                continue
            is_test = is_test_path(module, path)
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
    known = set()
    for delta in specs.deltas:
        for doc in (delta.doc, delta.living):
            if doc:
                known |= {r.id for r in doc.requirements} | {s.id for r in doc.requirements for s in r.scenarios}
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
