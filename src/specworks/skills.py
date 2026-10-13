"""Install the packaged agent skills into a project."""

from __future__ import annotations

from importlib import resources
from pathlib import Path


def packaged_skills() -> list[str]:
    root = resources.files("specworks").joinpath("skills")
    return sorted(entry.name for entry in root.iterdir() if entry.joinpath("SKILL.md").is_file())


def install_skills(target: Path, overwrite: bool = True) -> list[Path]:
    """Copy every packaged skill to ``target/<skill>/SKILL.md``; return written files."""
    written = []
    root = resources.files("specworks").joinpath("skills")
    for name in packaged_skills():
        dest = target / name / "SKILL.md"
        if dest.exists() and not overwrite:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(root.joinpath(name, "SKILL.md").read_text(encoding="utf-8"), encoding="utf-8")
        written.append(dest)
    return written
