"""Install the packaged agent skills into a project, for each supported AI tool.

Skills follow the Agent Skills format (``<name>/SKILL.md`` with ``name`` and
``description`` frontmatter), which Claude Code and GitHub Copilot both read:

- claude:  ``.claude/skills/<name>/SKILL.md``
- copilot: ``.github/skills/<name>/SKILL.md`` plus ``.github/prompts/<name>.prompt.md``
  so each phase is also a slash command in Copilot Chat (VS Code, JetBrains, ...).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from ..core.errors import SpecworksError

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


class ToolError(SpecworksError):
    """Raised for unknown tool ids."""


def packaged_skills() -> list[str]:
    root = resources.files("specworks").joinpath("skills")
    return sorted(entry.name for entry in root.iterdir() if entry.joinpath("SKILL.md").is_file())


# Text several skills share lives once in skills/_shared/<name>.md; a skill marks where it
# goes with a line ``<!-- specworks:include <name> -->``, filled in when the skill is read.
INCLUDE_RE = re.compile(r"^<!-- specworks:include (?P<name>[a-z0-9-]+) -->\n", re.MULTILINE)
# Every skill pre-approves the same ways of running the CLI (see _shared/running-cli.md):
# ``allowed-tools: SPECWORKS_CLI, Read, ...`` in a packaged skill.
CLI_TOOLS_TOKEN = "SPECWORKS_CLI"
CLI_TOOLS = "Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*)"
# Each installed file carries the hash of what was written, so a later install can tell a file
# the user edited (kept, unless --force) from one it wrote (replaced).
STAMP = "<!-- specworks:generated sha256={} -->\n"
STAMP_RE = re.compile(r"^<!-- specworks:generated sha256=(?P<hash>[0-9a-f]{64}) -->\n", re.MULTILINE)


def read_skill(name: str) -> str:
    """A packaged skill's SKILL.md with its shared parts and CLI tools filled in."""
    skills = resources.files("specworks").joinpath("skills")
    text = skills.joinpath(name, "SKILL.md").read_text(encoding="utf-8")
    text = INCLUDE_RE.sub(lambda m: skills.joinpath("_shared", f"{m.group('name')}.md").read_text(encoding="utf-8"), text)
    return text.replace(CLI_TOOLS_TOKEN, CLI_TOOLS)


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


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stamp(text: str) -> str:
    """``text`` with the generated-file stamp right after its frontmatter (which must stay first)."""
    match = FRONTMATTER_RE.match(text)
    at = match.end() if match else 0
    return text[:at] + STAMP.format(_digest(text)) + text[at:]


def is_edited(text: str) -> bool:
    """An installed file whose content no longer matches its stamp; an unstamped file is an older install, not an edit."""
    match = STAMP_RE.search(text)
    return match is not None and _digest(text[: match.start()] + text[match.end() :]) != match.group("hash")


def rendered_skills(root: Path, tools: list[Tool]) -> list[tuple[Path, str]]:
    """Every file installing the packaged skills for ``tools`` writes at ``root``, with its content."""
    files = []
    for name in packaged_skills():
        text = read_skill(name)
        for tool in tools:
            files.append((root / tool.skills_dir / name / "SKILL.md", stamp(render_skill(text, tool))))
            if tool.prompts_dir:
                files.append((root / tool.prompts_dir / f"{name}.prompt.md", stamp(render_prompt(text))))
    return files


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


def install_skills(root: Path, tools: list[Tool], force: bool = False) -> tuple[list[Path], list[Path]]:
    """Write every packaged skill (and Copilot prompt files) for ``tools``: (written, kept because the user edited them).

    ``force`` replaces edited files too.
    """
    written, kept = [], []
    for dest, text in rendered_skills(root, tools):
        if not force and dest.is_file() and is_edited(dest.read_text(encoding="utf-8", errors="replace")):
            kept.append(dest)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        written.append(dest)
    return written, kept


def outdated_skills(root: Path) -> list[Path]:
    """Installed skill files (of any tool) that `specworks skills` would replace: they differ from what this
    version of specworks installs and were not edited by hand (those are the user's now)."""
    outdated = []
    for dest, text in rendered_skills(root, list(TOOLS.values())):
        current = dest.read_text(encoding="utf-8", errors="replace") if dest.is_file() else text
        if current != text and not is_edited(current):
            outdated.append(dest)
    return outdated
