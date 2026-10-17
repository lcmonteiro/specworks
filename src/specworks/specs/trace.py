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

Tests are always scanned; ``source_globs``, when set, limit the other files. Without ``source_globs``, documentation (``.md``,
``.rst``, ``.txt``, ...) is not scanned: a tag quoted in a README or a note is
not code or a test. Globs that name such files scan them.

Globs follow the usual rules: ``*`` and ``?`` stay within one folder, ``**``
spans any number of folders (``tests/**/*.py`` includes ``tests/test_x.py``).
A tag may list several IDs: ``# @ac AC-AUTH-001.1, AC-AUTH-001.2``.
"""

from __future__ import annotations

import difflib
import os
import re
from dataclasses import dataclass, field, replace
from functools import cached_property
from pathlib import Path

from ..core.changes import Change
from ..core.workspace import Module, Workspace
from .check import ChangeSpecs, Issue, check_change, other_deltas
from .specfile import id_prefix

TAG_ID = r"(?:REQ|AC)-[A-Z0-9][A-Z0-9.-]*[A-Z0-9]"
TAG_RE = re.compile(rf"@(?P<kind>req|ac)\s+(?P<ids>{TAG_ID}(?:\s*,\s*{TAG_ID})*)")
SKIP_DIRS = {"node_modules", "__pycache__", "venv", "dist", "build", "target", "out", "vendor", "site-packages"}
# Not "spec"/"specs": they often hold source (spec parsers, OpenAPI specs); RSpec files
# are still found by name (``*_spec.rb``).
TEST_DIRS = {"test", "tests", "__tests__", "testing"}
TEST_NAME_RE = re.compile(r"(^test_|_test\.|\.test\.|\.spec\.|Test\.|Tests\.|_spec\.)")
MAX_FILE_BYTES = 1_000_000
DOC_EXTENSIONS = {".md", ".markdown", ".mdx", ".rst", ".txt", ".adoc", ".asciidoc", ".org"}


@dataclass
class Tag:
    id: str
    kind: str  # "req" or "ac"
    file: str
    line: int
    is_test: bool
    hint: str = ""  # an unknown tag: why, when it is more than "not in the specs" (e.g. an unknown prefix)

    @property
    def where(self) -> str:
        return f"{self.file}:{self.line}"

    @property
    def at(self) -> str:
        return f"{self.id} at {self.where}" + (f" ({self.hint})" if self.hint else "")


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


def glob_match(rel: str, pattern: str) -> bool:
    """``rel`` (a posix path) matches ``pattern``: ``*``/``?`` within one folder, ``**`` across folders."""
    regex = re.escape(pattern).replace(r"\*\*/", "(?:.*/)?").replace(r"\*\*", ".*").replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
    return re.fullmatch(regex, rel) is not None


def is_test_file(rel: str, test_globs: list[str]) -> bool:
    if test_globs:
        return any(glob_match(rel, g) for g in test_globs)
    parts = rel.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME_RE.search(parts[-1]))


def scan_rule(module: Module, path: Path) -> tuple[bool, bool]:
    """(scanned, is_test) for a file of ``module``: its tests (by test_globs, or by name outside docs) are always
    scanned; source_globs, when set, limit the other files; otherwise everything but documentation is scanned."""
    cfg = module.config
    rel = path.relative_to(module.root).as_posix()
    is_doc = path.suffix.lower() in DOC_EXTENSIONS
    if is_test_file(rel, cfg.test_globs) and (cfg.test_globs or not is_doc):
        return True, True
    if cfg.source_globs:
        return any(glob_match(rel, g) for g in cfg.source_globs), False
    return not is_doc, False


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
        for name in sorted(filenames):
            path = here / name
            scanned, is_test = scan_rule(module, path)
            if not scanned:
                continue
            # The path as walked, not resolved: a symlink to a file outside the workspace is not a crash.
            rel = path.relative_to(ws.root).as_posix()
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "@req" not in text and "@ac" not in text:
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                for match in TAG_RE.finditer(line):
                    for tag_id in re.findall(TAG_ID, match.group("ids")):
                        tags.append(Tag(id=tag_id, kind=match.group("kind"), file=rel, line=number, is_test=is_test))
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
        for sc in req.scenarios if req.section != "REMOVED" else []:
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
        # A criterion that goes with its block at close (left out of a MODIFIED one, or under a
        # REMOVED requirement) must leave the tests too, or they point to an ID no spec has.
        for sc in delta.dropped_criteria(req):
            ac_id = str(sc.id)
            rows.append(
                Row(
                    **{**base, "section": "REMOVED"},
                    ac=ac_id,
                    ac_title=sc.title,
                    tasks=tasks_by_id.get(ac_id, []),
                    tests=tests_by_id.get(ac_id, []),
                    code=code_by_id.get(ac_id, []),
                )
            )
    return rows


def _task_key(num: str) -> tuple[int, ...]:
    return tuple(int(p) for p in num.split("."))


# Each gap ``gaps`` reports, with how the trace and review outputs name it.
GAP_LABELS = {
    "acWithoutTasks": "acceptance criteria without a task",
    "acWithoutTests": "acceptance criteria without a test (`@ac`)",
    "reqWithoutCode": "requirements without code (`@req`)",
    "removedStillTagged": "removed requirements or criteria still tagged in tests or code",
}


def gaps(rows: list[Row]) -> dict[str, list[str]]:
    active = [r for r in rows if r.section != "REMOVED"]
    return {
        "acWithoutTasks": [r.ac for r in active if r.ac and not r.tasks],
        "acWithoutTests": [r.ac for r in active if r.ac and not r.tests],
        "reqWithoutCode": sorted({r.req for r in active if not r.code}),
        "removedStillTagged": sorted({r.ac or r.req for r in rows if r.section == "REMOVED" and (r.tests or r.code)}),
    }


def unknown_tags(specs: ChangeSpecs, tags: list[Tag], others: set[str], prefixes: set[str]) -> list[Tag]:
    """Tags to an ID no spec has: one of this change's capabilities without that ID in its delta, its living spec or
    another active change's delta (``others``), or a prefix no capability uses (``prefixes``: registered ones and
    those of every active change), which is a typo whatever change looks."""
    mine = {d.cap.prefix for d in specs.deltas}
    known = specs.known_ids() | others
    found = []
    for tag in tags:
        prefix = id_prefix(tag.id)
        if prefix is None:
            found.append(replace(tag, hint="not a REQ-<prefix>-NNN or AC-<prefix>-NNN.<n> ID"))
        elif prefix not in prefixes:
            close = difflib.get_close_matches(prefix, sorted(prefixes), n=1)
            found.append(replace(tag, hint=f"no capability uses the prefix {prefix}" + (f"; did you mean {close[0]}?" if close else "")))
        elif prefix in mine and tag.id not in known:
            found.append(tag)
    return found


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
        out += ["", "## Removed", "", "| Capability | Requirement or criterion | Tasks | Still tagged in |", "|---|---|---|---|"]
        out += [
            f"| {r.capability} | {f'{r.ac} {r.ac_title}' if r.ac else f'{r.req} {r.title}'} | {', '.join(r.tasks) or '—'} | {cell(r.tests + r.code)} |"
            for r in removed
        ]
    out += ["", "## Gaps", ""]
    out += [f"- {GAP_LABELS[k].capitalize()}: {', '.join(v)}" for k, v in found.items() if v] or ["- None"]
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

    @property
    def spec_warnings(self) -> list[str]:
        return [str(i) for i in self.issues if i.level == "warning"]

    @cached_property
    def tags(self) -> list[Tag]:
        return scan_tags(self.ws)

    @cached_property
    def rows(self) -> list[Row]:
        return build_matrix(self.specs, self.tags)

    @cached_property
    def gaps(self) -> dict[str, list[str]]:
        return gaps(self.rows)

    @cached_property
    def unknown_tags(self) -> list[Tag]:
        others = other_deltas(self.ws, self.change)
        prefixes = set(self.ws.prefixes()) | {d.cap.prefix for d in self.specs.deltas} | {cap.prefix for cap, _ in others}
        return unknown_tags(self.specs, self.tags, {i for _, doc in others for i in doc.ids()}, prefixes)
