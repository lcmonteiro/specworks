"""The git repository and a change's branch: requiring a repo, naming the branch, planning and creating it."""

import pytest

from helpers import git, init_repo
from specworks.core.git import GitError, GitMissing, branch_name, create_branch, git_text, plan_branch, require_repo


@pytest.fixture(autouse=True)
def identity(monkeypatch):
    for key, value in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def repo(tmp_path):
    """A repository on main with one commit."""
    init_repo(tmp_path)
    (tmp_path / "base.txt").write_text("base\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def current(root):
    return git_text(root, "branch", "--show-current").strip()


def commit_of(root, ref):
    return git_text(root, "rev-parse", ref).strip()


def branches(root):
    return git_text(root, "branch", "--format=%(refname:short)").split()


# @ac AC-PROJ-017.1
def test_a_folder_in_a_repository_passes_at_the_root_and_below(repo):
    require_repo(repo)
    (repo / "services/billing").mkdir(parents=True)
    require_repo(repo / "services/billing")
    require_repo(repo / "not/created/yet")  # a folder that does not exist yet: the nearest existing parent counts


# @ac AC-PROJ-017.2
def test_a_folder_outside_a_repository_is_refused_and_no_repository_is_made(tmp_path):
    with pytest.raises(GitError) as error:
        require_repo(tmp_path)
    assert not isinstance(error.value, GitMissing)
    assert "git init" in str(error.value) and "not inside a git repository" in str(error.value)
    assert not (tmp_path / ".git").exists()


# @ac AC-PROJ-017.3
def test_a_missing_git_is_refused_naming_the_failure(tmp_path, monkeypatch):
    empty = tmp_path / "empty-path"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    with pytest.raises(GitMissing) as error:
        require_repo(tmp_path)
    assert str(error.value).strip() and isinstance(error.value, GitError)
    assert not (tmp_path / ".git").exists()


# @ac AC-PROJ-018.1
def test_a_top_level_change_gets_a_branch_of_its_own_name(repo):
    assert branch_name("add-login") == "add-login"
    create_branch(repo, plan_branch(repo, branch_name("add-login")))
    assert "add-login" in branches(repo) and current(repo) == "add-login"


# @ac AC-PROJ-018.2
def test_a_module_change_gets_a_branch_with_a_slash_for_the_colon(repo):
    assert branch_name("billing:add-login") == "billing/add-login"
    assert branch_name("billing/tax:add-login") == "billing/tax/add-login"
    create_branch(repo, plan_branch(repo, branch_name("billing/tax:add-login")))
    assert current(repo) == "billing/tax/add-login"


# @ac AC-PROJ-018.3
def test_an_existing_branch_is_refused_and_nothing_changes(repo):
    git(repo, "branch", "add-login")
    before = branches(repo)
    with pytest.raises(GitError) as error:
        plan_branch(repo, "add-login")
    assert "add-login" in str(error.value)
    assert current(repo) == "main" and branches(repo) == before


# @ac AC-PROJ-019.1
def test_the_branch_starts_at_head_and_the_working_tree_comes_along(repo):
    (repo / "base.txt").write_text("edited\n")  # a modified tracked file
    (repo / "notes.txt").write_text("new\n")  # an untracked file
    branch = plan_branch(repo, "add-login", "main")
    assert current(repo) == "main"  # planning changes nothing
    create_branch(repo, branch)
    assert current(repo) == "add-login" and commit_of(repo, "add-login") == commit_of(repo, "main")
    assert (repo / "base.txt").read_text() == "edited\n" and (repo / "notes.txt").read_text() == "new\n"
    status = git_text(repo, "status", "--porcelain").splitlines()
    assert " M base.txt" in status and "?? notes.txt" in status


# @ac AC-PROJ-019.1
def test_the_branch_starts_at_the_current_head_when_it_is_not_main(repo):
    git(repo, "checkout", "-q", "-b", "feature")
    (repo / "feature.txt").write_text("f\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "feature work")
    create_branch(repo, plan_branch(repo, "add-login", "main"))
    assert commit_of(repo, "add-login") == commit_of(repo, "feature") != commit_of(repo, "main")


# @ac AC-PROJ-019.2
def test_a_detached_head_is_refused_and_no_branch_is_made(repo):
    git(repo, "checkout", "-q", "--detach")
    before = branches(repo)
    with pytest.raises(GitError) as error:
        plan_branch(repo, "add-login", "main")
    assert "detached" in str(error.value) and "switch to a branch" in str(error.value)
    assert branches(repo) == before and "add-login" not in branches(repo)


# @ac AC-PROJ-019.3
def test_the_branch_it_starts_from_is_named_unless_it_is_the_base(repo):
    git(repo, "checkout", "-q", "-b", "feature")
    assert plan_branch(repo, "add-login", "main").started_from == "feature"
    assert plan_branch(repo, "add-login", "main").name == "add-login"
    git(repo, "checkout", "-q", "main")
    assert plan_branch(repo, "add-login", "main").started_from is None
    assert plan_branch(repo, "add-login", "origin/main").started_from is None  # origin/main counts as main


# @ac AC-PROJ-019.3
def test_without_a_base_the_start_is_not_named(repo):
    git(repo, "checkout", "-q", "-b", "feature")
    assert plan_branch(repo, "add-login").started_from is None
    assert plan_branch(repo, "add-login", None).started_from is None


# @ac AC-PROJ-019.4
def test_a_repository_without_commits_still_gets_the_branch(tmp_path):
    init_repo(tmp_path)
    branch = plan_branch(tmp_path, "add-login", "main")
    create_branch(tmp_path, branch)
    assert current(tmp_path) == "add-login"
