"""The base of every error specworks reports to the user (bad config, unknown change, ...)."""


class SpecworksError(Exception):
    """An expected failure with a message for the user; the CLI prints it (or its JSON) and exits 1."""
