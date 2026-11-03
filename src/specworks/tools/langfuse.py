"""The Langfuse client: telemetry settings from the config and the environment, and sending a change's unsent events.

Only the ``SPECWORKS_LANGFUSE_*`` variables are read, never the plain ``LANGFUSE_*`` ones, and the keys
are never written, printed or put in an error. Sending uses the public ingestion API with the standard library only.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from ..core.changes import Change
from ..core.config import TelemetryConfig

DEFAULT_HOST = "https://cloud.langfuse.com"
TIMEOUT = 5.0  # seconds per request
BATCH_SIZE = 100  # events per ingestion request
ENV_PUBLIC_KEY = "SPECWORKS_LANGFUSE_PUBLIC_KEY"
ENV_SECRET_KEY = "SPECWORKS_LANGFUSE_SECRET_KEY"
ENV_HOST = "SPECWORKS_LANGFUSE_HOST"


@dataclass(frozen=True)
class LangfuseSettings:
    """Whether telemetry is ``on``, opted in with ``keys missing`` (named in ``missing``), or ``off``; the keys stay out of ``repr``.

    Implements REQ-INTEG-008.
    """

    state: Literal["on", "keys missing", "off"]
    host: str
    missing: tuple[str, ...] = ()
    public_key: str = field(default="", repr=False)
    secret_key: str = field(default="", repr=False)


def langfuse_settings(config: TelemetryConfig | None, env: Mapping[str, str] | None = None) -> LangfuseSettings:
    """The telemetry settings from the top level's ``telemetry`` block and ``env`` (``os.environ`` when None).

    Implements REQ-INTEG-008.
    """
    raise NotImplementedError


@dataclass(frozen=True)
class SendResult:
    """How many events were sent, how many are still queued, and why not all were sent (None when they were).

    Implements REQ-INTEG-009.
    """

    sent: int
    queued: int
    reason: str | None


def send_events(change: Change, settings: LangfuseSettings, trace: str, session: str, module_label: str) -> SendResult:
    """Send the change's unsent events to Langfuse in batches, marking each accepted batch sent.

    Stops at the first failed batch; never raises for a network or server failure. Implements REQ-INTEG-009.
    """
    raise NotImplementedError
