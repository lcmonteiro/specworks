# Review: upgrade-project

Base: `origin/main`

## Findings

- [ ] R1 **quality** `update` puts its `--tools` option inline in the signature, `def update(tools: str | None = typer.Option(\n    ...\n)) -> None:`. Every other command in the file puts each parameter on its own line, as `init` does (`src/specworks/cli/project.py:150`)
  - **Decision**: back to code: lay out the signature like `init`'s (one parameter per line, closing `) -> None:` on its own line); no behaviour change

## Changed files without tags

- None: `specworks review` lists no untagged code or test files. `README.md` (the Upgrade part, task 4.1) is documentation.

## Summary

The code matches the specs in both directions: REQ-INTEG-006 (`skills_state`, `installed_tools`, `expected_skills`), REQ-CLI-009 (`update_skills`, `specworks update`) and REQ-CLI-004 (the skills state in `context`), with every criterion tested.
- `install_skills` and `remove_stale_skills` are rebuilt on the shared `expected_skills` / `_stale_files`, so writing and comparing cannot drift; the AC-INTEG-005.x tests still pass.
- Checked by hand: an unknown `--tools` and running outside a project fail with the usual errors, `context` takes 0.23 s, and branch coverage is 98%.

One layout finding goes back to code.
