# specworks

**Spec-driven development for AI coding agents.** specworks gives an agent
(Claude Code, GitHub Copilot) a workflow to follow, one skill per phase, and a
CLI that checks every step:

```text
refine → specify → design → test → code → review → validate → close
```

![specworks workflow: solid arrows move forward when a phase's gate passes, dashed arrows go back](diagrams/workflow.svg)

Every requirement gets an ID (`REQ-LINK-001`), every acceptance criterion a
test tagged `@ac AC-LINK-001.1`, every implementation a tag `@req REQ-LINK-001`.
The CLI follows those links from spec to test to code, and a phase only ends
when its **gate** passes.

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Getting started
:link: getting-started
:link-type: doc

Install specworks, set up a project and run your first change.
:::

:::{grid-item-card} Concepts
:link: concepts/index
:link-type: doc

You, the skill and the CLI; phases and gates; IDs, tags and traceability.
:::

:::{grid-item-card} Tutorial
:link: tutorial/index
:link-type: doc

An example project through every phase, with the real output of every command
and how each output feeds the skill.
:::

:::{grid-item-card} Skills
:link: skills/index
:link-type: doc

What each `/specworks-*` skill does, step by step, and the commands it runs.
:::

:::{grid-item-card} CLI reference
:link: cli/index
:link-type: doc

Every `specworks` command: options, exit codes, text and JSON output.
:::

:::{grid-item-card} Reference
:link: reference/index
:link-type: doc

Configuration, every gate and validate check, review findings, the run cache,
troubleshooting.
:::
::::

```{toctree}
:hidden:
:caption: Start here

getting-started
walkthrough
```

```{toctree}
:hidden:
:caption: Understand

concepts/index
tutorial/index
```

```{toctree}
:hidden:
:caption: Use

skills/index
cli/index
reference/index
```

```{toctree}
:hidden:
:caption: Develop

api/index
development
simulation-report
```
