# specworks

[![CI](https://github.com/lcmonteiro/specworks/actions/workflows/ci.yml/badge.svg)](https://github.com/lcmonteiro/specworks/actions/workflows/ci.yml)

Spec-driven development for AI coding agents, inspired by
[OpenSpec](https://github.com/Fission-AI/OpenSpec) and written in Python (managed with `uv`).
The agent (Claude Code, GitHub Copilot) follows one skill per phase, and the `specworks`
CLI checks every step: each requirement has an ID, each acceptance criterion a test tagged
`@ac`, each implementation a tag `@req`, and a phase ends only when its gate passes.

**Documentation: the [wiki](https://github.com/lcmonteiro/specworks/wiki)**

```
refine -> specify -> design -> implement (test | code) -> review -> validate -> close
```

![specworks workflow: solid arrows move forward when a phase's gate passes, dashed arrows go back](assets/workflow.svg)

| Phase     | Skill                  | Output |
|-----------|------------------------|--------|
| refine    | `/specworks-refine`    | `refinement.md`: problem, context, constraints, options, recommendation |
| specify   | `/specworks-specify`   | `proposal.md`, delta specs (requirements + acceptance criteria), `design.md`, `tasks.md`, `traceability.md` |
| design    | `/specworks-design`    | the API decided with you (new and extended classes, functions, signatures, errors), recorded under Interfaces in `design.md` and created as empty stubs that build |
| implement | `/specworks-test`      | the test half: failing tests tagged `@ac` for every acceptance criterion, written against those stubs (`[test]` tasks) |
| implement | `/specworks-code`      | the code half, independent of the test half: real code replacing the stubs, `@req` tags, existing tests green (`[code]` tasks) |
| review    | `/specworks-review`    | finds drift between code, spec and design/API, proposes a change to whichever is wrong (applied with you, or sent back to `specify`, `design`, `implement`, or one of its halves `test` or `code`), records every decision in `review.md` |
| validate  | `/specworks-validate`  | **read-only** PASS/FAIL report (completeness, correctness, coherence); every failure names the phase that fixes it |
| close     | `/specworks-close`     | deltas merged into the living `spec.md`, `requirements.md` regenerated, design / architecture / diagrams updated in `<capability-path>/docs/`, change archived (phase `done`) |

The flow is not strictly linear: the dashed arrows are the ways back, to `specify`
when the spec turns out wrong, and to the phase that fixes each review finding or
failed validate check.

## Install

```bash
uv tool install git+https://github.com/lcmonteiro/specworks
```

The install includes [D2](https://d2lang.com) for diagrams, through the pinned
[`pyd2`](https://github.com/lcmonteiro/pyd2) dependency, so every machine renders
identical SVGs. Set `SPECWORKS_D2` to use another `d2`.

### Upgrade

```bash
uv tool upgrade specworks   # the CLI
specworks update            # in each project: its agent skills, to match the CLI
```

`specworks context` says `skills out of date: run specworks update` when a
project's skills differ from the ones the CLI installs.

## Quick start

```bash
cd your-project
specworks init   # writes .specworks/config.yml, .specworks/changes/active/ and archive/, and the agent skills
```

Then, in your agent:

1. **`/specworks-start`** in a repository with no code yet: it recommends
   the tooling, proposes the structure (one project or several modules, with their
   capabilities and code folders) and creates it once you approve the tree. Or
   **`/specworks-adopt`** on a project that already has code: it finds the test and
   lint commands from the build files and CI, writes a short `context`, and maps the
   code to capabilities with you.
2. **`/specworks-refine <what you want>`**: explore the problem and the options.
3. **`/specworks-specify`**: requirements and acceptance criteria, confirmed with you,
   then design notes and tasks.
4. **`/specworks-build`**: design → implement (test | code) → review, in cycles until the review is clean.
5. **`/specworks-done`**: the final check (`/specworks-validate`) and, only if it
   passes, the requirements merged into the living spec next to the code
   (`/specworks-close`). The two skills also run on their own.

The [walkthrough](https://github.com/lcmonteiro/specworks/wiki/Walkthrough) follows one small change through every
phase in five minutes.

**`/specworks-adopt`** stops once the capabilities are mapped. Then each capability
gets its living spec, one at a time:

```
/specworks-adopt
for each capability:
    /specworks-baseline <capability>
    /specworks-done baseline-<capability>     # validate, then close
```

**`/specworks-baseline`** records the behaviour the code already has as a
`baseline-<capability>` change: requirements read from the existing tests and code,
confirmed with you, `@ac` / `@req` tags added, no behaviour change. Suspected bugs
are left out, each a candidate for its own change. `/specworks-done` validates it,
writes the capability's living spec and names the next capability to baseline.

**`/specworks-build`** runs design → implement (test | code) → review in one go, each
phase exactly as its own skill, with the test and code halves in parallel. When the
review has findings, it asks whether to start a new cycle, which runs only the steps
the findings need: the code half, the test half, both halves, or design then both
halves, then review; a spec finding stops the build and hands over to
`/specworks-specify`.

**`/specworks-done`** finishes a reviewed change: it runs `/specworks-validate` and,
only on PASS, `/specworks-close`, each exactly as its own skill. A FAIL stops before
anything is closed and names the phase to go back to.

## AI tools

The skills use the open [Agent Skills](https://agentskills.io) format, so the same
files work in several tools:

| Tool | Installed files | How to run a phase |
|------|-----------------|--------------------|
| Claude Code | `.claude/skills/specworks-*/SKILL.md` | `/specworks-refine` or just ask ("let's refine ...") |
| GitHub Copilot | `.github/skills/specworks-*/SKILL.md`, or `.claude/skills/` when Claude Code is chosen too (Copilot reads both) | `/specworks-refine` in Copilot Chat (agent mode), or just ask |

`specworks init` asks which tools the project uses (in a terminal, with the
detected ones as the default) and saves the answer as `tools:` in
`.specworks/config.yml`; `--tools claude,copilot`, `--tools all` or
`--tools auto` chooses without asking. Each skill is installed once, in the
fewest folders the chosen tools read. `specworks skills` re-installs them for
the saved tools, e.g. after upgrading specworks. The skills call the
`specworks` CLI, so the agent needs terminal access.

## Learn more

| | |
|---|---|
| [Concepts](https://github.com/lcmonteiro/specworks/wiki/Concepts) | you, the skill and the CLI; how each command's output feeds the skill; phases and gates; capabilities, IDs, tags and traceability; modules |
| [Tutorial](https://github.com/lcmonteiro/specworks/wiki/Tutorial) | an example project through every phase and two changes, with the real output of every command |
| [Skills](https://github.com/lcmonteiro/specworks/wiki/Skills) | each skill step by step: the commands it runs and what it decides from their output |
| [CLI reference](https://github.com/lcmonteiro/specworks/wiki/CLI) | every `specworks` command: options, exit codes, text and JSON output |
| [Reference](https://github.com/lcmonteiro/specworks/wiki/Reference) | configuration, every gate and validate check, review findings, the run cache, troubleshooting |

## Development

```bash
uv sync
uv run pytest
uv run ruff check src tests   # lint
uv run mypy                   # typecheck
uv run coverage run -m pytest && uv run coverage report   # branch coverage; CI fails under 95%
```

The code layout, how to edit the wiki
and how to update pyd2 are on the [Development](https://github.com/lcmonteiro/specworks/wiki/Development) page.
