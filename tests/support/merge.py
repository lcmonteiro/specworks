"""
Helpers shared by the merge tests of several capabilities.
"""

from helpers import REF, git, run_json
from specworks.core.git import git_text

CHANGE = f".specworks/changes/active/{REF}"
TASKS_MD = f"{CHANGE}/tasks.md"
BRANCH = "half"
BASELINE = "baseline"


def make_halves(project, monkeypatch):
    """
    The planned project committed on main (tagged `baseline`), with the change's trace written, and a `half` branch from there; on main.
    """
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)
    (project / "src/auth/session.py").write_text("def session():\n    return 1\n")
    run_json("trace", "--change", REF, "--write")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "baseline")
    git(project, "tag", BASELINE)
    git(project, "branch", BRANCH)
    return project


def commit_on(root, branch, files, message):
    """
    Check out `branch`, write `files` ({relative path: text}), commit them.
    """
    git(root, "checkout", "-q", branch)
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)


def tick(root, *numbers):
    """
    The baseline's tasks.md with the given tasks ticked, whatever is checked out, so each side carries only its own edits.
    """
    text = git_text(root, "show", f"{BASELINE}:{TASKS_MD}")
    for n in numbers:
        text = text.replace(f"- [ ] {n} ", f"- [x] {n} ")
    return text


def head(root):
    return git_text(root, "rev-parse", "HEAD").strip()


def status(root):
    return git_text(root, "status", "--porcelain").strip()


def merging(root):
    return (root / ".git/MERGE_HEAD").exists()


def snapshot(root):
    """
    HEAD and the text of every file git knows, to check an aborted merge left the checkout as it was.
    """
    files = git_text(root, "ls-files").split()
    return head(root), {f: (root / f).read_text(encoding="utf-8") for f in files}
