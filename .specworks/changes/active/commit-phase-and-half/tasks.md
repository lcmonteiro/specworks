# Tasks: commit-phase-and-half

## 1. The subject of a phase commit (project)

- [x] 1.1 Add `phase_subject(ref, change, half=None, message=None) -> str` as a stub in `src/specworks/core/changes.py`, and rename `commit_phase`'s `subject` to `message` and add `half=None` (REQ-PROJ-036, REQ-PROJ-024); update the CLI call in `src/specworks/cli/changes.py` to the new keyword; verify `specworks run lint`
- [ ] 1.2 [test] In `tests/project/test_commit.py`, write failing tests tagged `@ac AC-PROJ-036.1` … `@ac AC-PROJ-036.10`: the subjects `add-login: review`, `add-login: implement (test)` / `(code)`, `add-login: implement (test) - cycle 2`, a message with the prefix kept, a blank message giving the prefix; the refusals (no half in implement, a half in review and after close, `docs`, a two-line message) leave the index empty and no new commit; `add-login: close - inspect` after close; verify they fail on the stub
- [ ] 1.3 [test] Update the AC-PROJ-024.3 test: with the message `stubs` in design the subject is `add-login: design - stubs`, the trailers after a blank line (`@ac AC-PROJ-024.3`); give `half` wherever an existing commit test runs in implement; verify it fails on the stub
- [ ] 1.4 [code] Implement `phase_subject` as design.md's "The rule, in order" (REQ-PROJ-036) tagged `@req REQ-PROJ-036`; verify `specworks run lint`
- [ ] 1.5 [code] In `commit_phase`, compute the subject with `phase_subject` before reading dirty files or staging (REQ-PROJ-024, REQ-PROJ-036) tagged `@req REQ-PROJ-024`; verify `specworks run lint`

## 2. `specworks commit --half` (cli)

- [x] 2.1 Add `--half` (`test` or `code`) to `specworks commit` as a stub option passed to `commit_phase`, and reword `--message`'s help to "text after the subject's prefix" (REQ-CLI-012); verify `uv run specworks commit --help` lists `--half`
- [ ] 2.2 [test] In `tests/cli/`, write failing tests tagged `@ac AC-CLI-012.8` and `@ac AC-CLI-012.9`: `--half code --message "cycle 2"` in implement returns `subject` `add-login: implement (code) - cycle 2` and `git log -1 --format=%s` agrees; no `--half` in implement prints `{"error": …}` naming `--half test` and `--half code`, exits 1 and makes no commit; give `--half` wherever an existing CLI commit test runs in implement; verify they fail on the stub
- [ ] 2.3 [code] Wire `--half` through and turn `ChangeError` from `commit_phase` into the CLI's error value (REQ-CLI-012) tagged `@req REQ-CLI-012`; verify `specworks run lint` and that `uv run specworks commit --change nope --half test --json` still names `nope`

## 3. The merge commit (workflow)

- [ ] 3.1 [test] In `tests/workflow/test_merge.py`, write failing tests tagged `@ac AC-FLOW-015.7`: a change in implement merging a branch `wt-test` with only test files, and one whose merge resolves `tasks.md`, each leave a merge commit whose subject is `<ref>: implement (merge <branch>)`; verify they fail on today's code (git's `Merge branch`)
- [ ] 3.2 [code] In `merge_branch`, compute `<ref>: <phase> (merge <branch>)` before merging and commit with it on both paths: `git merge --no-ff -m <subject>` and, after resolving, `git commit -m <subject>` (REQ-FLOW-015) tagged `@req REQ-FLOW-015`; verify `specworks run lint`

## 4. The skills commit with the new subject (skill text)

- [ ] 4.1 [test] In `tests/test_skills.py`, write failing tests for design.md's Pinned wording (REQ-PROJ-036, REQ-FLOW-015): the shared committing text's two phrases in every skill that includes it; `specworks commit --change "<ref>" --half test` in specworks-test and `--half code` in specworks-code; `--half test` in specworks-build's worktree commit; `specworks commit --change "<ref>" --message "inspect"` in specworks-inspect, and no `--message "<ref>: inspect"`; verify they fail on today's skills
- [ ] 4.2 [code] Edit `src/specworks/skills/_shared/committing.md`, `specworks-test`, `specworks-code`, `specworks-build` and `specworks-inspect` with the Pinned wording (REQ-PROJ-036), then `uv run specworks skills` to refresh `.claude/skills/`; verify `git diff --stat .claude/skills` shows the refreshed copies

## Workflow follow-up

- The harness's `/merge` (REQ-HARNESS-007) gets the new merge subject through `merge_branch`; its own tests only check the files and branches, so none should change.
