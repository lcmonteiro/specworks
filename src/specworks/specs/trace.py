# specworks: ignore-tags-start
"""
Traceability: requirement -> acceptance criteria -> tasks -> tests -> code.

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

Sample tags that are not the project's own (fixtures a test writes, examples in
a docstring) are kept out with markers, in any comment syntax: the tags on a
line holding ``specworks: ignore-tags`` are skipped, and so are the lines from
a line holding only ``specworks: ignore-tags-start`` to one holding only
``specworks: ignore-tags-end`` (or to the end of the file). A marker quoted in
prose, like these, counts for nothing. Skipped tags count neither as tests or
code nor as unknown tags.
"""
# specworks: ignore-tags-end

from __future__ import annotations

import difflib
import os
import re
from dataclasses import dataclass, field, replace
from functools import cached_property
from pathlib import Path
from typing import Any

from specworks.core.changes import ARCHIVE_DIR, META_FILE, Change
from specworks.core.git import GitError, git_text
from specworks.core.workspace import Module, Workspace
from specworks.specs.capabilities import CapabilityRef
from specworks.specs.check import ChangeSpecs, Issue, check_change, other_deltas
from specworks.specs.specfile import id_prefix, parse_spec, table_cell

TAG_ID = r"(?:REQ|AC)-[A-Z0-9][A-Z0-9.-]*[A-Z0-9]"
TAG_RE = re.compile(rf"@(?P<kind>req|ac)\s+(?P<ids>{TAG_ID}(?:\s*,\s*{TAG_ID})*)")
SKIP_DIRS = {"node_modules", "__pycache__", "venv", "dist", "build", "target", "out", "vendor", "site-packages"}
# Not "spec"/"specs": they often hold source (spec parsers, OpenAPI specs); RSpec files
# are still found by name (``*_spec.rb``).
TEST_DIRS = {"test", "tests", "__tests__", "testing"}
TEST_NAME_RE = re.compile(r"(^test_|_test\.|\.test\.|\.spec\.|Test\.|Tests\.|_spec\.)")
MAX_FILE_BYTES = 1_000_000
DOC_EXTENSIONS = {".md", ".markdown", ".mdx", ".rst", ".txt", ".adoc", ".asciidoc", ".org"}
IGNORE_LINE_RE = re.compile(r"specworks: ignore-tags(?![-\w])")
IGNORE_START, IGNORE_END = "specworks: ignore-tags-start", "specworks: ignore-tags-end"


@dataclass
class Tag:
    id: str
    kind: str  # "req" or "ac"
    file: str
    line: int
    is_test: bool
    hint: str = ""  # why an unknown tag is unknown, e.g. an unknown prefix

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
    changed: list[str] = field(default_factory=list)  # the test and code locations whose file changed since a closed change's close (REQ-SPECS-018)


@dataclass(frozen=True)
class ChangedSince:
    """
    What changed since a closed change's close: the close ``commit`` and the ``files`` changed since (committed or
    not, relative to the workspace root); without git or without that commit, ``commit`` is None, ``files`` is empty
    and ``note`` says why.

    Implements REQ-SPECS-018.
    """

    commit: str | None
    files: frozenset[str]
    note: str = ""


# @req REQ-SPECS-018
def changed_since_close(ws: Workspace, change: Change) -> ChangedSince:
    """
    The files changed since the close of the archived ``change``: the close commit is the last commit that added its
    archive folder (its ``.change.yaml``, which only the close adds: an inspection.md written later adds a file to the
    folder too), and the files are those ``git diff --name-only <commit>`` lists, with the untracked ones.

    Implements REQ-SPECS-018.
    """
    meta = f"{ws.rel(change.path)}/{META_FILE}"
    try:
        # --no-renames: the close moves the folder, which git would otherwise read as a rename, not an addition.
        commit = git_text(ws.root, "log", "-1", "--no-renames", "--diff-filter=A", "--format=%H", "--", meta).strip()
        if not commit:
            return ChangedSince(None, frozenset(), f"no commit adds {meta}: cannot tell what changed since the close")
        changed = git_text(ws.root, "-c", "core.quotepath=off", "diff", "--name-only", "--relative", commit, "--")
        untracked = git_text(ws.root, "-c", "core.quotepath=off", "ls-files", "--others", "--exclude-standard")
    except GitError as exc:
        reason = str(exc).splitlines()[0] if str(exc) else "git failed"
        return ChangedSince(None, frozenset(), f"cannot tell what changed since the close ({reason})")
    return ChangedSince(commit, frozenset(line for line in (changed + "\n" + untracked).splitlines() if line.strip()))


# @req REQ-SPECS-018
def mark_changed(rows: list[Row], since: ChangedSince) -> None:
    """
    Set each row's ``changed``: its test and code locations (``file:line``) whose file is in ``since.files``.
    """
    for row in rows:
        row.changed = [where for where in row.tests + row.code if where.rsplit(":", 1)[0] in since.files]


# @req REQ-SPECS-018
def living_spec_at(ws: Workspace, change: Change, cap: CapabilityRef, commit: str | None) -> str | None:
    """
    The text of ``cap``'s living spec as it was at ``commit``, read with ``git show <commit>:<living spec>``; None
    without the commit, without git, or when the spec did not exist then. The trace of a closed change compares its
    MODIFIED and REMOVED blocks with it, so a criterion a later change added is never reported as removed.

    Implements REQ-SPECS-018.
    """
    living = cap.living_spec()
    if commit is None or living is None:
        return None
    try:
        rel = living.resolve().relative_to(ws.root.resolve()).as_posix()
        # ./ reads the path from the workspace root, which may be a folder inside the repository.
        return git_text(ws.root, "show", f"{commit}:./{rel}")
    except (GitError, ValueError):
        return None


# @req REQ-SPECS-011
def glob_match(rel: str, pattern: str) -> bool:
    """
    ``rel`` (a posix path) matches ``pattern``: ``*``/``?`` within one folder, ``**`` across folders.
    """
    regex = re.escape(pattern).replace(r"\*\*/", "(?:.*/)?").replace(r"\*\*", ".*").replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
    return re.fullmatch(regex, rel) is not None


def is_test_file(rel: str, test_globs: list[str]) -> bool:
    if test_globs:
        return any(glob_match(rel, g) for g in test_globs)
    parts = rel.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME_RE.search(parts[-1]))


# @req REQ-SPECS-011
def scan_rule(module: Module, path: Path) -> tuple[bool, bool]:
    """
    (scanned, is_test) for a file of ``module``: its tests (by test_globs, or by name outside docs) are always
    scanned; source_globs, when set, limit the other files; otherwise everything but documentation is scanned.
    """
    cfg = module.config
    rel = path.relative_to(module.root).as_posix()
    is_doc = path.suffix.lower() in DOC_EXTENSIONS
    if is_test_file(rel, cfg.test_globs) and (cfg.test_globs or not is_doc):
        return True, True
    if cfg.source_globs:
        return any(glob_match(rel, g) for g in cfg.source_globs), False
    return not is_doc, False


def _is_marker(line: str, marker: str) -> bool:
    """
    ``marker`` alone on the line, around comment punctuation only: a doc that quotes it in prose is not one.
    """
    return marker in line and not any(ch.isalnum() for ch in line.replace(marker, "", 1))


# @req REQ-SPECS-001, REQ-SPECS-002
def _tag_lines(text: str) -> list[tuple[int, str]]:
    """
    (number, line) of the lines whose tags count: not marked ``specworks: ignore-tags`` and not inside an
    ignore block (``ignore-tags-start`` .. ``ignore-tags-end``, or the end of the file).
    """
    lines, ignoring = [], False
    for number, line in enumerate(text.splitlines(), start=1):
        if _is_marker(line, IGNORE_START):
            ignoring = True
        elif _is_marker(line, IGNORE_END):
            ignoring = False
        elif not ignoring and not IGNORE_LINE_RE.search(line):
            lines.append((number, line))
    return lines


# @req REQ-SPECS-003, REQ-SPECS-011
def scan_tags(ws: Workspace) -> list[Tag]:
    """
    Every @req / @ac tag in the workspace, skipping hidden, vendored and workflow folders.
    """
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
            for number, line in _tag_lines(text):  # ignored lines never become tags, so no check sees them
                for match in TAG_RE.finditer(line):
                    for tag_id in re.findall(TAG_ID, match.group("ids")):
                        tags.append(Tag(id=tag_id, kind=match.group("kind"), file=rel, line=number, is_test=is_test))
    return tags


# @req REQ-SPECS-012
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
        base: dict[str, Any] = dict(capability=delta.cap.ref, req=req_id, title=req.title, section=req.section)
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


# @req REQ-SPECS-012
def gaps(rows: list[Row]) -> dict[str, list[str]]:
    active = [r for r in rows if r.section != "REMOVED"]
    return {
        "acWithoutTasks": [r.ac for r in active if r.ac and not r.tasks],
        "acWithoutTests": [r.ac for r in active if r.ac and not r.tests],
        "reqWithoutCode": sorted({r.req for r in active if not r.code}),
        "removedStillTagged": sorted({r.ac or r.req for r in rows if r.section == "REMOVED" and (r.tests or r.code)}),
    }


# @req REQ-SPECS-012
def unknown_tags(specs: ChangeSpecs, tags: list[Tag], others: set[str], prefixes: set[str]) -> list[Tag]:
    """
    Tags to an ID of this change's capabilities that no spec has (``others``: other active changes' IDs), or with a
    prefix no capability uses.
    """
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


# @req REQ-SPECS-012
def to_markdown(change_ref: str, rows: list[Row], found: dict[str, list[str]]) -> str:
    """
    The matrix as markdown; a location in its row's ``changed`` (a closed change's, REQ-SPECS-018) is marked ``(changed since close)``.
    """
    changed = {where for r in rows for where in r.changed}

    def cell(items: list[str]) -> str:
        return "<br>".join(f"`{i}`" + (" (changed since close)" if i in changed else "") for i in items) if items else "—"

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
        ac = f"{r.ac} {table_cell(r.ac_title)}".strip() if r.ac else "—"
        out.append(
            f"| {r.capability} | {r.req} {table_cell(r.title)} ({r.section}) | {ac} | {', '.join(r.tasks) or '—'} | {cell(r.tests)} | {cell(r.code)} |"
        )
    removed = [r for r in rows if r.section == "REMOVED"]
    if removed:
        out += ["", "## Removed", "", "| Capability | Requirement or criterion | Tasks | Still tagged in |", "|---|---|---|---|"]
        out += [
            f"| {r.capability} | {f'{r.ac} {table_cell(r.ac_title)}' if r.ac else f'{r.req} {table_cell(r.title)}'} | {', '.join(r.tasks) or '—'} | {cell(r.tests + r.code)} |"
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
    """
    What the CLI knows about a change: its parsed specs and their issues, the workspace's tags and the gaps.

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

    @property
    def archived(self) -> bool:
        """
        The change is in its module's archive folder (closed or abandoned): its trace marks what changed since.
        """
        return self.change.path.parent.name == ARCHIVE_DIR

    # @req REQ-SPECS-018
    @cached_property
    def changed_since(self) -> ChangedSince | None:
        """
        What changed since an archived change's close; None for an active change.
        """
        return changed_since_close(self.ws, self.change) if self.archived else None

    # @req REQ-SPECS-018
    def _specs_at_close(self) -> ChangeSpecs:
        """
        The specs with each delta's living spec as it was before the close (at the close commit's parent): the close
        commit already holds the merged spec, without the criteria the change left out. None without that commit, so no
        criterion is reported as removed rather than one guessed from today's spec.
        """
        commit = self.changed_since.commit if self.changed_since else None
        parent = f"{commit}^" if commit else None
        deltas = []
        for delta in self.specs.deltas:
            text = living_spec_at(self.ws, self.change, delta.cap, parent)
            deltas.append(replace(delta, living=parse_spec(text) if text is not None else None))
        return replace(self.specs, deltas=deltas)

    @cached_property
    def rows(self) -> list[Row]:
        # A closed change's removed criteria come from the living spec just before its close, not from today's (REQ-SPECS-018).
        rows = build_matrix(self._specs_at_close() if self.archived else self.specs, self.tags)
        if self.changed_since is not None:
            mark_changed(rows, self.changed_since)
        return rows

    @cached_property
    def gaps(self) -> dict[str, list[str]]:
        return gaps(self.rows)

    @cached_property
    def unknown_tags(self) -> list[Tag]:
        others = other_deltas(self.ws, self.change)
        prefixes = set(self.ws.prefixes()) | {d.cap.prefix for d in self.specs.deltas} | {cap.prefix for cap, _ in others}
        return unknown_tags(self.specs, self.tags, {i for _, doc in others for i in doc.ids()}, prefixes)
