# Review: add-branch-default

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **spec-gap** REQ-CLI-015 says stayedOn is none 'outside a git repository', but new refuses any folder outside a repository first (REQ-CLI-006, REQ-PROJ-017; require_repo at src/specworks/cli/changes.py:31), so that case never happens; and REQ-CLI-006, not modified by the delta, still says new creates the branch 'unless --no-branch is given', so the living spec would contradict REQ-CLI-015 once closed
  - **Proposal**: back to specify: in REQ-CLI-015 drop 'outside a git repository or' (stayedOn is none only with a detached HEAD); add REQ-CLI-006 as MODIFIED (whole block) saying the branch is created unless --no-branch is given or the workspace's branch_per_change is false (REQ-CLI-015). No code change
  - **Decision**: back to specify: drop 'outside a git repository' from REQ-CLI-015 and modify REQ-CLI-006 so the branch also follows branch_per_change
  - done in specify: REQ-CLI-015 no longer names an outside-git case; REQ-CLI-006 modified to name branch_per_change; task 3.1/3.2 confirm its tests and tag
  - done in design: no API change: REQ-CLI-006 is reworded only; design.md's Interfaces says so
  - done in implement: code: new already carries @req REQ-CLI-006 next to REQ-CLI-015; no code change
  - confirmed in review: confirmed in cycle 2: REQ-CLI-015 names no outside-git case; REQ-CLI-006 is MODIFIED to name branch_per_change; new carries @req REQ-CLI-006 and REQ-CLI-015; the AC-CLI-006 tests pass unchanged
- [x] R2 **spec-gap** config set branch_per_change writes the current module's config, or --module's (REQ-CLI-013; set_config_value(target.root, ...) at src/specworks/cli/project.py:376), but REQ-PROJ-026 ignores a module's own branch_per_change: run from inside a module, the command reports success and changes nothing
  - **Proposal**: back to specify: REQ-CLI-013 (MODIFIED) says branch_per_change is always written to the top level's config, whatever the current module or --module, and the output names that config's path; add its criterion (from inside module billing, config set branch_per_change false changes only the top config and ws.top.config.branch_per_change is false); then design and both halves follow (config_set passes ws.top.root for that key)
  - **Decision**: back to specify: REQ-CLI-013 always writes branch_per_change to the top level's config (whatever the current module or --module), with a new criterion
  - done in specify: REQ-CLI-013 modified: branch_per_change is always written to the top level's config; added AC-CLI-013.6 and tasks 3.1/3.2
  - done in design: design.md: config_set targets ws.top for branch_per_change, output names the top level; signature unchanged, no stub needed
  - done in implement: code: config_set writes branch_per_change to ws.top's config whatever the current module or --module; output names the top level (src/specworks/cli/project.py)
  - confirmed in review: confirmed in cycle 2: config_set targets ws.top for branch_per_change (src/specworks/cli/project.py:368); AC-CLI-013.6's test covers inside billing's folder and --module billing, and passes
- [x] R3 **quality** config set's help does not list the new key: the KEY argument says 'context, or commands.<test|lint|typecheck|build|format>' and the docstring 'Set a command or the context' (src/specworks/cli/project.py:355 and :361)
  - **Proposal**: back to code: name branch_per_change (true|false) in the KEY help and the docstring
  - **Decision**: back to code: name branch_per_change in config set's key help and docstring
  - done in code: config set's KEY help and docstring name branch_per_change (true|false, top level's config)
  - confirmed in review: confirmed in cycle 2: config set's KEY help and docstring name branch_per_change (src/specworks/cli/project.py:355, :361)
- [ ] R4 **spec-gap** with a detached HEAD and new staying (branch_per_change false, or --no-branch), the code creates the change with branch and stayedOn null (current_branch returns None, src/specworks/core/git.py:103; new at src/specworks/cli/changes.py:42), as REQ-CLI-015 says ('none with a detached HEAD'); but REQ-CLI-006 (MODIFIED) still says new SHALL fail, creating nothing, when HEAD is detached (AC-CLI-006.8), without limiting that to creating the branch, so the two requirements contradict each other; and no criterion covers the detached stay, so its path (git.py:107-110) has no test
  - **Proposal**: back to specify: reword REQ-CLI-006 so the existing-branch and detached-HEAD failures apply when new creates the branch (staying on a detached HEAD creates the change, REQ-CLI-015), AC-CLI-006.8 likewise; add AC-CLI-015.6 (GIVEN branch_per_change false and a detached HEAD, WHEN new add-login --json runs, THEN the change is created, HEAD is still detached, and branch and stayedOn are null); then the test half adds its test. No code change
  - **Decision**: back to specify: limit REQ-CLI-006's detached-HEAD and existing-branch failures to creating the branch, add AC-CLI-015.6 for staying on a detached HEAD; the test half adds its test, no code change
  - done in specify: REQ-CLI-006 and AC-CLI-006.8 limit the detached-HEAD and existing-branch failures to creating the branch; added AC-CLI-015.6 and task 4.1
  - done in design: no API change: REQ-CLI-006 is reworded and AC-CLI-015.6 is reached through new's existing branch/stayedOn fields; design.md's Interfaces says so
  - done in implement: code: no code change; new already stays on a detached HEAD with branch and stayedOn null (current_branch returns None) and refuses a detached HEAD only when it creates the branch (plan_branch), as reworded REQ-CLI-006 and AC-CLI-015.6 say

## Changed files without tags

None: `specworks review` lists no untraced source or test files; every changed file carries `@req` / `@ac` tags.

## Summary

The suite passes (812 tests) and every requirement and criterion is tagged; the code follows design.md's Interfaces and Decisions. Two spec gaps go back to specify: REQ-CLI-015's impossible 'outside a git repository' case with REQ-CLI-006 left unmodified (R1), and `config set branch_per_change` writing a module's config, where the key is ignored (R2). R3 (config set's help) goes back to code. No fixes applied in review (inside /specworks-build).

Cycle 2: R1, R2 and R3 are carried out and confirmed (814 tests pass). One new spec gap: staying on a detached HEAD creates the change, as REQ-CLI-015 says, while REQ-CLI-006 says new fails with a detached HEAD, and no criterion or test covers that path (R4, proposed back to specify; no code change).
