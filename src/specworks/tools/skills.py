"""Install the packaged agent skills into a project, for each supported AI tool.

Skills follow the Agent Skills format (``<name>/SKILL.md`` with ``name`` and
``description`` frontmatter), which Claude Code and GitHub Copilot both read:

- claude:  ``.claude/skills/<name>/SKILL.md``
- copilot: ``.github/skills/<name>/SKILL.md`` plus ``.github/prompts/<name>.prompt.md``
  so each phase is also a slash command in Copilot Chat (VS Code, JetBrains, ...).
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Literal

from ..core.errors import SpecworksError

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    skills_dir: str  # the folder it prefers, written when no folder picked for another chosen tool is in ``reads``
    # Every skills folder this tool reads, ``skills_dir`` first.
    reads: tuple[str, ...] = ()
    prompts_dir: str | None = None
    # Files or folders whose presence means the project already uses this tool.
    detect: tuple[str, ...] = field(default_factory=tuple)
    # Frontmatter keys this tool understands; others are dropped from its copy.
    keep_keys: tuple[str, ...] = ("name", "description", "allowed-tools")


TOOLS: dict[str, Tool] = {
    "claude": Tool(
        id="claude",
        label="Claude Code",
        skills_dir=".claude/skills",
        reads=(".claude/skills",),
        detect=(".claude", "CLAUDE.md"),
    ),
    "copilot": Tool(
        id="copilot",
        label="GitHub Copilot",
        skills_dir=".github/skills",
        reads=(".github/skills", ".claude/skills", ".agents/skills"),
        prompts_dir=".github/prompts",
        detect=(
            ".github/copilot-instructions.md",
            ".github/instructions",
            ".github/prompts",
            ".github/skills",
            ".github/agents",
        ),
        # allowed-tools lists Claude Code tool names; Copilot has its own tool set.
        keep_keys=("name", "description"),
    ),
}


# Copilot prompt files: none is written any more; specworks ones left by an older version are removed.
PROMPTS_DIR = ".github/prompts"


class ToolError(SpecworksError):
    """Raised for unknown tool ids."""


def packaged_skills() -> list[str]:
    root = resources.files("specworks").joinpath("skills")
    return sorted(entry.name for entry in root.iterdir() if entry.joinpath("SKILL.md").is_file())


# Text several skills share lives once in skills/_shared/<name>.md; a skill marks where it
# goes with a line ``<!-- specworks:include <name> -->``, filled in when the skill is read.
INCLUDE_RE = re.compile(r"^<!-- specworks:include (?P<name>[a-z0-9-]+) -->\n", re.MULTILINE)


# @req REQ-INTEG-005
def read_skill(name: str) -> str:
    """A packaged skill's SKILL.md with its shared parts filled in."""
    skills = resources.files("specworks").joinpath("skills")
    text = skills.joinpath(name, "SKILL.md").read_text(encoding="utf-8")
    return INCLUDE_RE.sub(lambda m: skills.joinpath("_shared", f"{m.group('name')}.md").read_text(encoding="utf-8"), text)


# @req REQ-INTEG-005
def split_frontmatter(text: str) -> tuple[list[tuple[str, str]], str]:
    """``---``-delimited frontmatter as ordered (key, lines) pairs, and the body after it.

    An indented line continues the key above it (a folded ``description: >``), so a key is kept or dropped whole.
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return [], text
    pairs: list[tuple[str, str]] = []
    for line in match.group(1).splitlines():
        if line.startswith((" ", "\t")) and pairs:
            pairs[-1] = (pairs[-1][0], pairs[-1][1] + "\n" + line)
        elif ":" in line:
            pairs.append((line.split(":", 1)[0].strip(), line))
    return pairs, text[match.end() :]


# @req REQ-INTEG-005
def render_skill(text: str, tool: Tool) -> str:
    pairs, body = split_frontmatter(text)
    kept = [line for key, line in pairs if key in tool.keep_keys]
    return "---\n" + "\n".join(kept) + "\n---\n" + body


# @req REQ-INTEG-005
def render_prompt(text: str) -> str:
    """Copilot prompt file: description frontmatter, agent mode, and the skill's instructions."""
    pairs, body = split_frontmatter(text)
    description = next((line for key, line in pairs if key == "description"), "description: ''")
    return f"---\n{description}\nagent: agent\n---\n{body}"


# @req REQ-INTEG-004
def parse_tools(value: str, root: Path) -> list[Tool]:
    """``auto`` (default), ``all`` or a comma list such as ``claude,copilot``.

    ``auto`` picks the tools the project already uses; when none is detected it
    installs for every supported tool.
    """
    value = value.strip().lower()
    if value == "all":
        return list(TOOLS.values())
    if value == "auto":
        detected = [t for t in TOOLS.values() if any((root / p).exists() for p in t.detect)]
        return detected or list(TOOLS.values())
    tools = []
    for item in filter(None, (part.strip() for part in value.split(","))):
        if item not in TOOLS:
            raise ToolError(f"unknown tool '{item}'; expected auto, all or a list of: {', '.join(TOOLS)}")
        tools.append(TOOLS[item])
    if not tools:
        raise ToolError("no tool given; use auto, all or a list such as claude,copilot")
    return tools


def resolve_tools(root: Path, saved: list[str] | None, given: str | None) -> tuple[list[Tool], bool]:
    """The tools to install for, and whether to save them in the config.

    ``given`` (``--tools``) wins and is saved; else the ``saved`` tool IDs; else the
    installed tools, else ``auto``, saved. Implements REQ-INTEG-004, REQ-CLI-009.
    """
    raise NotImplementedError


def skill_folders(tools: list[Tool]) -> list[tuple[Tool, str]]:
    """The fewest skills folders every tool in ``tools`` reads, each with the tool whose frontmatter keys its copies keep.

    Tools are taken in ``TOOLS`` order; a tool gets its preferred folder only when no folder
    picked so far is in its ``reads``. Implements REQ-INTEG-005.
    """
    raise NotImplementedError


# Skills shipped before every skill took the specworks- prefix; removed like any stale specworks-* skill.
RETIRED_NAMES: tuple[str, ...] = ("sw-refine",)


def _stale(name: str, shipped: set[str]) -> bool:
    """A specworks skill name (its prefix, or a retired one) that this version does not ship; any other name is not ours."""
    return (name.startswith("specworks-") or name in RETIRED_NAMES) and name not in shipped


# @req REQ-INTEG-005
def remove_stale_skills(root: Path, tools: list[Tool]) -> list[Path]:
    """Delete the specworks skills (and Copilot prompt files) of ``tools`` that are no longer shipped; return what was deleted."""
    removed = []
    for rel in _stale_files(root, tools):
        path = root / rel
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()  # a prompt file, or only the link: its target is not ours to delete
        removed.append(path)
    return removed


# @req REQ-INTEG-005
def install_skills(root: Path, tools: list[Tool]) -> list[Path]:
    """Write every packaged skill (and Copilot prompt files) for ``tools``; return written files."""
    written = []
    for rel, text in expected_skills(tools).items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        written.append(dest)
    return written


@dataclass(frozen=True)
class SkillFile:
    """An installed skill or prompt file that differs from what this version installs."""

    path: str  # relative to the workspace root, with /
    reason: Literal["changed", "missing", "stale"]


@dataclass(frozen=True)
class SkillsState:
    """How the installed skills compare with this version's: current, outdated (with the files) or none installed."""

    state: Literal["current", "outdated", "none"]
    files: list[SkillFile] = field(default_factory=list)


# @req REQ-INTEG-005, REQ-INTEG-006
def expected_skills(tools: list[Tool]) -> dict[str, str]:
    """Every skill file (and Copilot prompt file) of ``tools`` this version installs: relative path -> text."""
    files = {}
    for tool in tools:
        for name in packaged_skills():
            text = read_skill(name)
            files[f"{tool.skills_dir}/{name}/SKILL.md"] = render_skill(text, tool)
            if tool.prompts_dir:
                files[f"{tool.prompts_dir}/{name}.prompt.md"] = render_prompt(text)
    return files


def _ours(name: str) -> bool:
    return name.startswith("specworks-") or name in RETIRED_NAMES


# @req REQ-INTEG-006
def installed_tools(root: Path) -> list[Tool]:
    """The tools whose skills folder holds a specworks skill."""
    def has_skills(tool: Tool) -> bool:
        folder = root / tool.skills_dir
        return folder.is_dir() and any(p.is_dir() and _ours(p.name) for p in folder.iterdir())

    return [tool for tool in TOOLS.values() if has_skills(tool)]


# @req REQ-INTEG-005, REQ-INTEG-006
def _stale_files(root: Path, tools: list[Tool]) -> list[str]:
    """Relative paths of the specworks skill folders and prompt files of ``tools`` this version no longer ships."""
    shipped, stale = set(packaged_skills()), []
    for tool in tools:
        skills = root / tool.skills_dir
        for folder in sorted(skills.iterdir()) if skills.is_dir() else []:
            if folder.is_dir() and _stale(folder.name, shipped):
                stale.append(f"{tool.skills_dir}/{folder.name}")
        prompts = root / tool.prompts_dir if tool.prompts_dir else None
        for prompt in sorted(prompts.glob("*.prompt.md")) if prompts and prompts.is_dir() else []:
            if _stale(prompt.name.removesuffix(".prompt.md"), shipped):
                stale.append(f"{tool.prompts_dir}/{prompt.name}")
    return stale


def _differs(path: Path, text: str) -> Literal["changed", "missing"] | None:
    """``missing`` or ``changed`` when the file at ``path`` is not ``text``; None when it is."""
    if not path.is_file():
        return "missing"
    return None if path.read_text(encoding="utf-8") == text else "changed"


# @req REQ-INTEG-006
def skills_state(root: Path, saved: list[str] | None = None) -> SkillsState:
    """Compare the installed skills of the project's tools with what this version installs.

    The tools are the ``saved`` tool IDs of the config, else every tool that has skills installed.
    Implements REQ-INTEG-006.
    """
    if saved is not None:
        raise NotImplementedError
    tools = installed_tools(root)
    if not tools:
        return SkillsState("none")
    files = [SkillFile(rel, reason) for rel, text in expected_skills(tools).items() if (reason := _differs(root / rel, text))]
    files += [SkillFile(rel, "stale") for rel in _stale_files(root, tools)]
    files.sort(key=lambda f: f.path)
    return SkillsState("outdated" if files else "current", files)


# @req REQ-CLI-009
def update_skills(root: Path, tools: list[Tool]) -> tuple[list[Path], list[Path]]:
    """Write the skill files of ``tools`` that differ or are missing and remove the stale ones; return (updated, removed)."""
    removed = remove_stale_skills(root, tools)
    updated = []
    for rel, text in expected_skills(tools).items():
        dest = root / rel
        if _differs(dest, text):
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
            updated.append(dest)
    return updated, removed
