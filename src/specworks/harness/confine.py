"""What a peer's shell may not do: push, or see the model's and the tracing keys."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping

#: A push: ``git``, then any global options (``-C x``, ``--no-pager``, ``-c a=b``), then the ``push`` subcommand.
PUSH_RE = re.compile(r"\bgit(\s+-{1,2}\S+(\s+[^-\s]\S*)?)*\s+push\b")

#: The variables a peer's shell never gets: the model's and the tracing keys.
HIDDEN_ENV = ("SPECWORKS_MODEL_", "SPECWORKS_LANGFUSE_")


# @req REQ-HARNESS-010
def shell_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """The environment of a peer's shell: ``env`` (default this process's), without ``HIDDEN_ENV``. Implements REQ-HARNESS-010."""
    return {k: v for k, v in (os.environ if env is None else env).items() if not k.startswith(HIDDEN_ENV)}


# @req REQ-HARNESS-008
def refuses(command: str) -> bool:
    """Whether the shell refuses ``command`` (a ``git push``). Implements REQ-HARNESS-008."""
    return PUSH_RE.search(command) is not None
