# Review: add-branch-default

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **spec-gap** REQ-CLI-015 says stayedOn is none 'outside a git repository', but new refuses any folder outside a repository first (REQ-CLI-006, REQ-PROJ-017; require_repo at src/specworks/cli/changes.py:31), so that case never happens; and REQ-CLI-006, not modified by the delta, still says new creates the branch 'unless --no-branch is given', so the living spec would contradict REQ-CLI-015 once closed
  - **Proposal**: back to specify: in REQ-CLI-015 drop 'outside a git repository or' (stayedOn is none only with a detached HEAD); add REQ-CLI-006 as MODIFIED (whole block) saying the branch is created unless --no-branch is given or the workspace's branch_per_change is false (REQ-CLI-015). No code change
  - **Decision**: back to specify: drop 'outside a git repository' from REQ-CLI-015 and modify REQ-CLI-006 so the branch also follows branch_per_change
- [ ] R2 **spec-gap** config set branch_per_change writes the current module's config, or --module's (REQ-CLI-013; set_config_value(target.root, ...) at src/specworks/cli/project.py:376), but REQ-PROJ-026 ignores a module's own branch_per_change: run from inside a module, the command reports success and changes nothing
  - **Proposal**: back to specify: REQ-CLI-013 (MODIFIED) says branch_per_change is always written to the top level's config, whatever the current module or --module, and the output names that config's path; add its criterion (from inside module billing, config set branch_per_change false changes only the top config and ws.top.config.branch_per_change is false); then design and both halves follow (config_set passes ws.top.root for that key)
- [ ] R3 **quality** config set's help does not list the new key: the KEY argument says 'context, or commands.<test|lint|typecheck|build|format>' and the docstring 'Set a command or the context' (src/specworks/cli/project.py:355 and :361)
  - **Proposal**: back to code: name branch_per_change (true|false) in the KEY help and the docstring

## Changed files without tags

None: `specworks review` lists no untraced source or test files; every changed file carries `@req` / `@ac` tags.

## Summary

The suite passes (812 tests) and every requirement and criterion is tagged; the code follows design.md's Interfaces and Decisions. Two spec gaps go back to specify: REQ-CLI-015's impossible 'outside a git repository' case with REQ-CLI-006 left unmodified (R1), and `config set branch_per_change` writing a module's config, where the key is ignored (R2). R3 (config set's help) goes back to code. No fixes applied in review (inside /specworks-build).
