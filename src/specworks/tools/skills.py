"""Install the packaged agent skills into a project, for each supported AI tool.

Skills follow the Agent Skills format (``<name>/SKILL.md`` with ``name`` and
``description`` frontmatter), which Claude Code and GitHub Copilot both read:

- claude:  ``.claude/skills/<name>/SKILL.md``
- copilot: ``.github/skills/<name>/SKILL.md`` plus ``.github/prompts/<name>.prompt.md``
  so each phase is also a slash command in Copilot Chat (VS Code, JetBrains, ...).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    skills_dir: str
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
        detect=(".claude", "CLAUDE.md"),
    ),
    "copilot": Tool(
        id="copilot",
        label="GitHub Copilot",
        skills_dir=".github/skills",
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


class ToolError(Exception):
    """Raised for unknown tool ids."""


def packaged_skills() -> list[str]:
    root = resources.files("specworks").joinpath("skills")
    return sorted(entry.name for entry in root.iterdir() if entry.joinpath("SKILL.md").is_file())


# Text several skills share lives once in skills/_shared/<name>.md; a skill marks where it
# goes with a line ``<!-- specworks:include <name> -->``, filled in when the skill is read.
INCLUDE_RE = re.compile(r"^<!-- specworks:include (?P<name>[a-z0-9-]+) -->\n", re.MULTILINE)


def read_skill(name: str) -> str:
    """A packaged skill's SKILL.md with its shared parts filled in."""
    skills = resources.files("specworks").joinpath("skills")
    text = skills.joinpath(name, "SKILL.md").read_text(encoding="utf-8")
    return INCLUDE_RE.sub(lambda m: skills.joinpath("_shared", f"{m.group('name')}.md").read_text(encoding="utf-8"), text)


def split_frontmatter(text: str) -> tuple[list[tuple[str, str]], str]:
    """``---``-delimited frontmatter as ordered (key, line) pairs, and the body after it."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return [], text
    pairs = [(line.split(":", 1)[0].strip(), line) for line in match.group(1).splitlines() if ":" in line]
    return pairs, text[match.end() :]


def render_skill(text: str, tool: Tool) -> str:
    pairs, body = split_frontmatter(text)
    kept = [line for key, line in pairs if key in tool.keep_keys]
    return "---\n" + "\n".join(kept) + "\n---\n" + body


def render_prompt(text: str) -> str:
    """Copilot prompt file: description frontmatter, agent mode, and the skill's instructions."""
    pairs, body = split_frontmatter(text)
    description = next((line for key, line in pairs if key == "description"), "description: ''")
    return f"---\n{description}\nagent: agent\n---\n{body}"


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


# Skills from before the phase rename (propose/interface/implement/verify); installing removes them.
RENAMED_SKILLS = ("specworks-propose", "specworks-interface", "specworks-implement", "specworks-verify")


def remove_renamed_skills(root: Path, tools: list[Tool]) -> list[Path]:
    """Delete the old skill files specworks installed under its former names; return what was removed."""
    removed = []
    for tool in tools:
        for name in RENAMED_SKILLS:
            skill = root / tool.skills_dir / name / "SKILL.md"
            prompt = root / tool.prompts_dir / f"{name}.prompt.md" if tool.prompts_dir else None
            for path in (skill, prompt):
                if path is not None and path.is_file():
                    path.unlink()
                    removed.append(path)
            if skill.parent.is_dir() and not any(skill.parent.iterdir()):
                skill.parent.rmdir()
    return removed


def install_skills(root: Path, tools: list[Tool]) -> list[Path]:
    """Write every packaged skill (and Copilot prompt files) for ``tools``; return written files."""
    written = []
    for tool in tools:
        for name in packaged_skills():
            text = read_skill(name)
            dest = root / tool.skills_dir / name / "SKILL.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(render_skill(text, tool), encoding="utf-8")
            written.append(dest)
            if tool.prompts_dir:
                prompt = root / tool.prompts_dir / f"{name}.prompt.md"
                prompt.parent.mkdir(parents=True, exist_ok=True)
                prompt.write_text(render_prompt(text), encoding="utf-8")
                written.append(prompt)
    return written
