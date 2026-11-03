"""Helpers shared by the skills tests of several capabilities."""

from typer.testing import CliRunner

from helpers import init_repo
from specworks.cli import app
from specworks.core.config import load_config
from specworks.tools.skills import skills_state

runner = CliRunner()
SKILL = "specworks-refine"


def init(tmp_path, monkeypatch, *args):
    monkeypatch.chdir(tmp_path)
    init_repo(tmp_path)
    result = runner.invoke(app, ["init", *args])
    assert result.exit_code == 0, result.output
    return result.output


def frontmatter(path):
    return path.read_text().split("---\n")[1]


def specworks_skills_in(folder):
    return sorted(p.name for p in folder.iterdir() if p.name.startswith("specworks-")) if folder.is_dir() else []


MULTILINE = (
    "---\nname: specworks-x\ndescription: >\n  Does x.\n  Use when: the user asks for x.\n"
    "allowed-tools: Bash(specworks:*),\n  Read\n---\n# Body\n"
)


def installed_files(root):
    return {p: p.read_text(encoding="utf-8") for d in (".claude", ".github") for p in (root / d).rglob("*") if p.is_file()}


def state_of(root):
    st = skills_state(root, load_config(root).tools)  # as the CLI computes it: with the saved tools
    return st.state, {(f.path, f.reason) for f in st.files}


# --- includes with parameters (REQ-INTEG-007) --------------------------------------------

def fake_shared(files):
    """A ``shared`` for ``fill_includes``: the text of each shared file by name."""
    return lambda name: files[name]
