"""Helpers shared by the archive tests of several capabilities."""

from datetime import date

from helpers import REF, run_json
from specworks.specs import merge

TODAY = date(2026, 6, 1)
ARCHIVED = f".specworks/changes/archive/{TODAY.isoformat()}-{REF}"


def make_fixed_today(monkeypatch):
    # Keeps ARCHIVED right when a run crosses midnight.
    class FixedDate(date):
        @classmethod
        def today(cls):
            return TODAY

    monkeypatch.setattr(merge, "date", FixedDate)


def abandon(reason="replaced by add-sso"):
    return run_json("abandon", "--change", REF, "--reason", reason)
