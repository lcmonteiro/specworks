# specworks

**Spec-driven development for AI coding agents.** specworks gives an agent
(Claude Code, GitHub Copilot) a workflow to follow, one skill per phase, and a
CLI that checks every step:

```text
refine → specify → design → test → code → review → validate → close
```

![specworks workflow: solid arrows move forward when a phase's gate passes, dashed arrows go back](images/workflow.svg)

Every requirement gets an ID (`REQ-LINK-001`), every acceptance criterion a
test tagged `@ac AC-LINK-001.1`, every implementation a tag `@req REQ-LINK-001`.
The CLI follows those links from spec to test to code, and a phase only ends
when its **gate** passes.

- **[Getting started](Getting-Started)**: Install specworks, set up a project and run your first change.

- **[Concepts](Concepts)**: You, the skill and the CLI; phases and gates; IDs, tags and traceability.

- **[Tutorial](Tutorial)**: An example project through every phase, with the real output of every command and how each output feeds the skill.

- **[Skills](Skills)**: What each `/specworks-*` skill does, step by step, and the commands it runs.

- **[CLI reference](CLI)**: Every `specworks` command: options, exit codes, text and JSON output.

- **[Reference](Reference)**: Configuration, every gate and validate check, review findings, the run cache, troubleshooting.
