"""The base of every error specworks reports to the user (the CLI prints its message and exits 1)."""


class SpecworksError(Exception):
    """An expected failure with a message for the user: bad config, unknown change, failed merge..."""
