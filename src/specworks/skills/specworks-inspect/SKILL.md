---
name: specworks-inspect
description: Inspect a change, open or closed - walk its scenarios most uncertain and important first, each with its code, its test and the design that argues for it, in a circle the reviewer breaks, and leave the reviewer's notes as findings in inspection.md only when there are any. Use when the user wants to read, audit or understand what a specworks change did, or says "inspect", "inspect the change", "walk me through the change" or "specworks inspect".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Read, Grep, Glob
---

Inspect: not written yet. This skill's steps are written in the code half of
implement (design.md's seven steps); until then it does nothing.

<!-- specworks:include running-cli -->

<!-- specworks:include asking-the-user -->

<!-- specworks:include picking-the-change -->

---

## Steps

1. **Pick the change**

   Pick the change (above). The other steps are written in the code half.
