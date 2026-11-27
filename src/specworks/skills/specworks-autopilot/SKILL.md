---
name: specworks-autopilot
description: Run a specified change from its current phase (specify, design, implement, review or validate) to a passed validate on its own, chaining specify, the build and validate in subagents, taking the option marked (recommended) at each stop, logging every decision in autopilot.md, and stopping before close with the hard decisions for the user to validate. Use when a specworks change has been refined and the user wants the rest of the flow up to validate to run unattended, or says "autopilot", "run it on its own" or "specworks autopilot".
allowed-tools: Bash(specworks:*), Bash(uv run specworks:*), Bash(uvx --from git+https://github.com/lcmonteiro/specworks specworks:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Read, Grep, Glob, Write, Edit, Agent
---

Autopilot: not written yet. This skill's body is written in the implement
phase of the change add-autopilot-skill.

<!-- specworks:include running-cli -->

<!-- specworks:include asking-the-user -->

<!-- specworks:include picking-the-change -->

---

## Steps

1. Pick the change (above). The rest is not written yet.
