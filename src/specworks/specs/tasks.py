"""tasks.md: tracked tasks (``- [ ] N.M description``) and ticking them off."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..core.errors import SpecworksError
from ..core.files import read_text
from .specfile import fenced, find_ids

TASKS_FILE = "tasks.md"
TASK_RE = re.compile(r"^(?P<lead>\s*- \[)(?P<mark>[^\]]*)(?P<close>\]\s+)(?P<num>\d+\.\d+)\s+(?P<text>\S.*)$")
TASKISH_RE = re.compile(r"^\s*[-*]\s*\[")
HALF_RE = re.compile(r"^\[(?P<half>test|code)\]", re.IGNORECASE)  # the half of implement a task belongs to
FOLLOW_UP_RE = re.compile(r"^##\s+Workflow follow-up\s*$", re.IGNORECASE)


class TaskError(SpecworksError):
    """Raised for a missing tasks.md or an unknown task number."""


@dataclass
class Task:
    num: str
    text: str
    done: bool
    line: int
    half: str = ""  # "test" or "code" from a leading [test] / [code] marker (which stays in text), else "" (REQ-SPECS-009)

    @property
    def ids(self) -> list[str]:
        return find_ids(self.text)

    def to_dict(self) -> dict:
        return {"num": self.num, "text": self.text, "done": self.done, "line": self.line, "ids": self.ids, "half": self.half}


# @req REQ-SPECS-009
def parse_tasks(text: str) -> tuple[list[Task], list[tuple[int, str]]]:
    tasks, problems = [], []
    lines = text.splitlines()
    for number, (line, example) in enumerate(zip(lines, fenced(lines), strict=True), start=1):
        if example:
            continue  # a task shown in a code fence is an example, not a tracked task
        if FOLLOW_UP_RE.match(line):
            break  # plain follow-up bullets are not tracked tasks
        if match := TASK_RE.match(line):
            done = match.group("mark").strip().lower() == "x"
            text = match.group("text")
            half = marker.group("half").lower() if (marker := HALF_RE.match(text)) else ""
            tasks.append(Task(num=match.group("num"), text=text, done=done, line=number, half=half))
        elif TASKISH_RE.match(line):
            problems.append((number, "task must be '- [ ] N.M description' (e.g. '- [ ] 1.2 Add the export endpoint')"))
    return tasks, problems


def read_tasks(change_path: Path) -> list[Task]:
    path = change_path / TASKS_FILE
    if not path.is_file():
        raise TaskError(f"{TASKS_FILE} is not written yet")
    return parse_tasks(read_text(path))[0]


# @req REQ-SPECS-009
def set_done(change_path: Path, nums: list[str], done: bool) -> None:
    """Tick (or untick) tasks by number, editing only their checkbox."""
    path = change_path / TASKS_FILE
    found = read_tasks(change_path)
    tasks = {t.num: t for t in found}
    unknown = [n for n in nums if n not in tasks]
    if unknown:
        raise TaskError(f"unknown task {', '.join(unknown)} (tasks: {', '.join(tasks) or 'none'})")
    twice = sorted({n for n in nums if sum(t.num == n for t in found) > 1})
    if twice:
        raise TaskError(f"task {', '.join(twice)} is numbered more than once in {TASKS_FILE}; renumber it first")
    lines = read_text(path, keep_newlines=True).splitlines(keepends=True)
    for num in nums:
        index = tasks[num].line - 1
        ending = lines[index][len(lines[index].rstrip("\r\n")) :]
        match = TASK_RE.match(lines[index].rstrip("\r\n"))
        assert match is not None  # read_tasks found a task on this line
        mark = "x" if done else " "
        lines[index] = f"{match.group('lead')}{mark}{match.group('close')}{match.group('num')} {match.group('text')}{ending}"
    path.write_text("".join(lines), encoding="utf-8", newline="")  # each line keeps its own ending
