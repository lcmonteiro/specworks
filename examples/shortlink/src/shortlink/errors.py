class ShortlinkError(Exception):
    """Base of every error shortlink raises."""


class InvalidUrl(ShortlinkError):
    """The URL is not an http(s) URL with a host. Implements REQ-LINK-001."""


class UnknownCode(ShortlinkError):
    """The code was not issued by this store. Implements REQ-LINK-002."""


class ExpiredCode(ShortlinkError):
    """The code's lifetime has ended. Implements REQ-LINK-002."""
