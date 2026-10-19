"""Reading project files: a file that cannot be read as UTF-8 text is a clear error, not a crash."""

from __future__ import annotations

from pathlib import Path

from .errors import SpecworksError


class FileError(SpecworksError):
    """Raised when a project file cannot be read as UTF-8 text."""


# @req REQ-PROJ-015
def read_text(path: Path, keep_newlines: bool = False) -> str:
    """The file's text; ``keep_newlines`` keeps its line endings (``\\r\\n``) instead of reading them as ``\\n``."""
    try:
        with path.open(encoding="utf-8", newline="" if keep_newlines else None) as file:
            return file.read()
    except UnicodeDecodeError as exc:
        raise FileError(f"{path} is not UTF-8 text ({exc.reason} at byte {exc.start}); save it as UTF-8") from None
    except OSError as exc:
        raise FileError(f"cannot read {path}: {exc.strerror or exc}") from None
