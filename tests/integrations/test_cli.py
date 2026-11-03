import pytest

from support.cli import make_project


@pytest.fixture
def project(tmp_path, monkeypatch):
    return make_project(tmp_path, monkeypatch)


# @ac AC-INTEG-005.1
def test_skills_are_installed_with_specworks_prefix(project):
    skills = sorted(p.name for p in (project / ".claude/skills").iterdir())
    assert skills and all(name.startswith("specworks-") for name in skills)
    text = (project / ".claude/skills/specworks-refine/SKILL.md").read_text()
    assert "name: specworks-refine" in text and "sw-" not in text
