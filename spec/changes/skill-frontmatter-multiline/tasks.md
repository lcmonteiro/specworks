# Tasks: skill-frontmatter-multiline

## 1. Multi-line frontmatter values

- [x] 1.1 Write failing tests in `tests/test_skills.py` for AC-INTEG-005.7 (a folded `description` with a `Use when:` line and a multi-line `allowed-tools`, rendered for Copilot, Claude Code and as a prompt file; plus every packaged skill rendered exactly as the one-line rule gives) tagged `@ac`; verify the multi-line test fails because the description's lines are lost
- [ ] 1.2 In `split_frontmatter`, attach each indented line to the key above it, so that a key is kept or dropped with its whole value (REQ-INTEG-005) tagged `@req REQ-INTEG-005`; verify the 1.1 tests and the existing AC-INTEG-005.x tests pass
