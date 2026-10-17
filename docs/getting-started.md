# Getting started

## Install

```console
$ uv tool install git+https://github.com/lcmonteiro/specworks
$ specworks version
0.1.0
```

The install includes [D2](https://d2lang.com) for diagrams, through the
[`pyd2`](https://github.com/lcmonteiro/pyd2) dependency pinned to one commit:
installing builds it for your platform, downloads the official D2 release it
pins and checks its SHA-256. Set `SPECWORKS_D2` to use another `d2`.

## Set up a project

In the project's root folder:

```console
$ specworks init --dir spec --tools claude
created spec.yml
ready   spec/changes/
tools   Claude Code
skill   .claude/skills/specworks-adopt/SKILL.md
skill   .claude/skills/specworks-build/SKILL.md
...
```

- `--dir spec` names the workflow folder (`spec/`) and the config (`spec.yml`).
  The default is `specworks`.
- `--tools` chooses where the agent skills go: `claude`
  (`.claude/skills/`), `copilot` (`.github/skills/` and `.github/prompts/`),
  `all`, or `auto` (the default: the tools the project already uses, all of
  them when none is found).

Then, in your agent, run **`/specworks-adopt`**. On a project that already has
code it finds the test and lint commands from the build files and CI, writes a
short `context`, and maps the code to **capabilities** with you. See
{doc}`skills/adopt`.

Or do it by hand: fill in `commands` and `context` in `spec.yml`
({doc}`reference/configuration`), then register each capability:

```console
$ specworks capability add links --path src/shortlink --prefix LINK --description "Create short codes for URLs and resolve them"
registered links -> src/shortlink (REQ-LINK-)
$ specworks run test
.                                                                        [100%]
1 passed in 0.00s
```

## Your first change

In the agent, one skill per phase. Each one ends by suggesting the next:

| You type | The agent | Ends with |
|---|---|---|
| `/specworks-refine let users shorten URLs` | explores the problem with you, compares options | `refinement.md` |
| `/specworks-specify` | writes the proposal, requirements (`REQ-…`) and acceptance criteria (`AC-…`), design notes, tasks; asks you to confirm the requirements | `gate specify` passed |
| `/specworks-build` | design (API as stubs, agreed with you) → test (failing `@ac` tests) → code (`@req` code, tests green) → review (drift between code, spec and design), in cycles | a clean review |
| `/specworks-validate` | the final read-only PASS/FAIL report | PASS |
| `/specworks-close` | merges the requirements into the living spec next to the code, archives the change | phase `done` |

You can also run the build phases one by one: `/specworks-design`,
`/specworks-test`, `/specworks-code`, `/specworks-review`.

```{tip}
Every skill drives the same CLI you can run yourself. `specworks status
--change <name>` shows where a change is; `specworks gate <phase> --change
<name>` tells you what is missing to finish a phase.
```

## Where to go next

- {doc}`walkthrough`: a five-minute tour of one change.
- {doc}`concepts/index`: how the pieces fit together.
- {doc}`tutorial/index`: every phase in depth, on an example project, with the
  real output of every command.
