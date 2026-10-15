"""tasks.md: tracked tasks (``- [ ] N.M description``) and ticking them off."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..core.errors import SpecworksError
from .specfile import find_ids

TASKS_FILE = "tasks.md"
TASK_RE = re.compile(r"^(?P<lead>\s*- \[)(?P<mark>[^\]]*)(?P<close>\]\s+)(?P<num>\d+\.\d+)\s+(?P<text>\S.*)$")
TASKISH_RE = re.compile(r"^\s*[-*]\s*\[")
FOLLOW_UP_RE = re.compile(r"^##\s+Workflow follow-up\s*$", re.IGNORECASE)


class TaskError(SpecworksError):
    """Raised for a missing tasks.md or an unknown task number."""


@dataclass
class Task:
    num: str
    text: str
    done: bool
    line: int

    @property
    def ids(self) -> list[str]:
        return find_ids(self.text)

    def to_dict(self) -> dict:
        return {"num": self.num, "text": self.text, "done": self.done, "line": self.line, "ids": self.ids}


def parse_tasks(text: str) -> tuple[list[Task], list[tuple[int, str]]]:
    tasks, problems = [], []
    for number, line in enumerate(text.splitlines(), start=1):
        if FOLLOW_UP_RE.match(line):
            break  # plain follow-up bullets are not tracked tasks
        if match := TASK_RE.match(line):
            done = match.group("mark").strip().lower() == "x"
            tasks.append(Task(num=match.group("num"), text=match.group("text"), done=done, line=number))
        elif TASKISH_RE.match(line):
            problems.append((number, "task must be '- [ ] N.M description' (e.g. '- [ ] 1.2 Add the export endpoint')"))
    return tasks, problems


def read_tasks(change_path: Path) -> list[Task]:
    path = change_path / TASKS_FILE
    if not path.is_file():
        raise TaskError(f"{TASKS_FILE} is not written yet")
    return parse_tasks(path.read_text(encoding="utf-8"))[0]


def set_done(change_path: Path, nums: list[str], done: bool) -> list[Task]:
    """Tick (or untick) tasks by number, editing only their checkbox; returns the updated tasks."""
    path = change_path / TASKS_FILE
    tasks = {t.num: t for t in read_tasks(change_path)}
    unknown = [n for n in nums if n not in tasks]
    if unknown:
        raise TaskError(f"unknown task {', '.join(unknown)} (tasks: {', '.join(tasks) or 'none'})")
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for num in nums:
        index = tasks[num].line - 1
        ending = lines[index][len(lines[index].rstrip("\r\n")) :]
        match = TASK_RE.match(lines[index].rstrip("\r\n"))
        assert match is not None  # read_tasks found a task on this line
        mark = "x" if done else " "
        lines[index] = f"{match.group('lead')}{mark}{match.group('close')}{match.group('num')} {match.group('text')}{ending}"
    path.write_text("".join(lines), encoding="utf-8")
    updated = {t.num: t for t in read_tasks(change_path)}
    return [updated[n] for n in nums]
