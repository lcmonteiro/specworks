**Pushing**: after the commit, offer to push the change's branch (the checked-out
one, from `git status`): ask `Push <branch>? (yes/no)`. On yes, run
`git push -u origin <branch>` (never pre-approved: the user is asked either
way) and relay the "create a pull request" link the remote prints. When it
prints none and `origin` is a `github.com` or `gitlab.com` URL, build the link:
`<repo URL>/pull/new/<branch>` for GitHub,
`<repo URL>/-/merge_requests/new?merge_request[source_branch]=<branch>` for
GitLab; otherwise only report the push. On no, say the branch stays local.
