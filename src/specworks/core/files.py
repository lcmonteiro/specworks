"""Reading project files: a file that cannot be read as UTF-8 text is a clear error, not a crash."""

from __future__ import annotations

from pathlib import Path

from .errors import SpecworksError


class FileError(SpecworksError):
    """Raised when a project file cannot be read as UTF-8 text."""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise FileError(f"{path} is not UTF-8 text ({exc.reason} at byte {exc.start}); save it as UTF-8") from None
    except OSError as exc:
        raise FileError(f"cannot read {path}: {exc.strerror or exc}") from None
