import secrets
import string
import time
from collections.abc import Callable
from urllib.parse import urlparse

from .errors import ExpiredCode, InvalidUrl, UnknownCode

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6


class LinkStore:
    """An in-memory store of short codes for URLs."""

    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._by_url: dict[str, str] = {}
        self._by_code: dict[str, str] = {}
        self._expires: dict[str, float] = {}

    # @req REQ-LINK-001, REQ-LINK-003
    def shorten(self, url: str, ttl: float | None = None) -> str:
        """Return the 6-character code of ``url``. Implements REQ-LINK-001.

        Raises InvalidUrl when ``url`` is not an http(s) URL with a host.
        """
        if ttl is not None and ttl <= 0:
            raise ValueError(f"ttl must be positive, got {ttl}")
        parts = urlparse(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise InvalidUrl(url)
        if url in self._by_url:
            return self._by_url[url]
        code = self._new_code()
        self._by_url[url] = code
        self._by_code[code] = url
        if ttl is not None:
            self._expires[code] = self._clock() + ttl
        return code

    # @req REQ-LINK-002
    def resolve(self, code: str) -> str:
        """Return the URL a code was issued for. Implements REQ-LINK-002.

        Raises UnknownCode when this store did not issue ``code``.
        """
        if code not in self._by_code:
            raise UnknownCode(code)
        if code in self._expires and self._clock() >= self._expires[code]:
            raise ExpiredCode(code)
        return self._by_code[code]

    def _new_code(self) -> str:
        while True:
            code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
            if code not in self._by_code:
                return code
