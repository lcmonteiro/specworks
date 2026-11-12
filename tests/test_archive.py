"""
Archived changes: abandon, list --archived, status, and names an archived change keeps.
"""

import shutil

import pytest

from helpers import REF
from support.archive import ARCHIVED, abandon, make_fixed_today


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    return make_fixed_today(monkeypatch)


def test_abandoning_twice_on_one_day_fails_without_moving(project):
    abandon()
    shutil.copytree(project / ARCHIVED, project / ".specworks/changes/active" / REF)
    code, data = abandon()
    assert code == 1 and "already exists in the archive" in data["error"]
    assert (project / ".specworks/changes/active" / REF).is_dir()
