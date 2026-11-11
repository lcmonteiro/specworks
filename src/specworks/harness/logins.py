"""The stored Copilot login: one global file and one file per project, in the user's config dir, never in a project."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Scope = Literal["global", "local"]


@dataclass(frozen=True)
class Login:
    """A GitHub OAuth token and its GitHub Enterprise host (empty for github.com); the token is hidden from ``repr``.

    Implements REQ-HARNESS-011.
    """

    oauth_token: str = field(repr=False)
    ghe_host: str = ""


def config_dir(env: Mapping[str, str] | None = None) -> Path:
    """The folder of the stored logins: ``$XDG_CONFIG_HOME`` or ``~/.config`` (``%APPDATA%`` on Windows), then ``specworks/copilot``.

    ``env`` is ``os.environ`` when None. Implements REQ-HARNESS-011.
    """
    raise NotImplementedError


class LoginStore:
    """Reads and writes the logins under ``base`` (``config_dir()`` when None). Implements REQ-HARNESS-011."""

    def __init__(self, base: Path | None = None) -> None:
        raise NotImplementedError

    def save(self, scope: Scope, root: Path | None, login: Login) -> None:
        """Write the ``scope`` login (``root`` is the project root, used by ``local``), owner-only, by rename. Implements REQ-HARNESS-011."""
        raise NotImplementedError

    def load(self, scope: Scope, root: Path | None) -> Login | None:
        """The ``scope`` login, or None when there is none. Implements REQ-HARNESS-011."""
        raise NotImplementedError

    def find(self, root: Path | None) -> Login | None:
        """The local login of ``root`` when there is one, else the global one, else None. Implements REQ-HARNESS-011."""
        raise NotImplementedError
