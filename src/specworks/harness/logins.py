"""The stored Copilot login: one global file and one file per project, in the user's config dir, never in a project."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
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


# @req REQ-HARNESS-011
def config_dir(env: Mapping[str, str] | None = None) -> Path:
    """The folder of the stored logins: ``$XDG_CONFIG_HOME`` or ``~/.config`` (``%APPDATA%`` on Windows), then ``specworks/copilot``.

    ``env`` is ``os.environ`` when None. Implements REQ-HARNESS-011.
    """
    env = os.environ if env is None else env
    home = Path(env.get("HOME") or env.get("USERPROFILE") or Path.home())
    if os.name == "nt":
        base = Path(env.get("APPDATA") or home / "AppData" / "Roaming")
    else:
        base = Path(env.get("XDG_CONFIG_HOME") or home / ".config")
    return base / "specworks" / "copilot"


# @req REQ-HARNESS-011
class LoginStore:
    """Reads and writes the logins under ``base`` (``config_dir()`` when None). Implements REQ-HARNESS-011."""

    def __init__(self, base: Path | None = None) -> None:
        self.base = config_dir() if base is None else base

    def _path(self, scope: Scope, root: Path | None) -> Path:
        if scope == "global":
            return self.base / "global.json"
        if root is None:
            raise ValueError("a local login needs the project root")
        key = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
        return self.base / "projects" / f"{key}.json"

    def save(self, scope: Scope, root: Path | None, login: Login) -> None:
        """Write the ``scope`` login (``root`` is the project root, used by ``local``), owner-only, by rename. Implements REQ-HARNESS-011."""
        path = self._path(scope, root)
        path.parent.mkdir(parents=True, exist_ok=True)
        for folder in (self.base, path.parent):
            folder.chmod(0o700)
        # mkstemp creates the file owner-only; the rename means a failed write keeps the earlier login.
        fd, temp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump({"oauth_token": login.oauth_token, "ghe_host": login.ghe_host}, handle)
            os.replace(temp, path)
        except BaseException:
            Path(temp).unlink(missing_ok=True)
            raise

    def load(self, scope: Scope, root: Path | None) -> Login | None:
        """The ``scope`` login, or None when there is none. Implements REQ-HARNESS-011."""
        try:
            data = json.loads(self._path(scope, root).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        token = data.get("oauth_token") if isinstance(data, dict) else None
        if not isinstance(token, str) or not token:
            return None
        host = data.get("ghe_host")
        return Login(token, host if isinstance(host, str) else "")

    def find(self, root: Path | None) -> Login | None:
        """The local login of ``root`` when there is one, else the global one, else None. Implements REQ-HARNESS-011."""
        local = self.load("local", root) if root is not None else None
        return local or self.load("global", None)
