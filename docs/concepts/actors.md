# You, the skill and the CLI

specworks splits the work between three actors.

| Actor | What it is | What it does | What it never does |
|---|---|---|---|
| **You** | the developer | decide product questions; confirm the requirements, the API, review decisions, merges | — |
| **The skill** | a `SKILL.md` file the agent follows (e.g. `.claude/skills/specworks-test/SKILL.md`) | reads code, talks with you, writes artifacts (specs, tests, code), runs the CLI and reacts to its output | invent paths or IDs; decide on its own that a phase is finished |
| **The CLI** | the `specworks` command | knows the paths, IDs and phases; parses specs, tasks, tags and `review.md`; runs your test and lint commands; says PASS or FAIL | write your code, tests or specs |

The rule behind every skill: **the skill decides, the CLI measures.** The skill
asks the CLI where a file goes and which ID comes next, writes the file, then
asks the CLI whether the result is valid. A phase is finished only when its
**gate** (`specworks gate <phase>`) passes.

```{mermaid}
sequenceDiagram
    actor U as You
    participant S as Skill (agent)
    participant C as specworks CLI
    participant F as Files (repo)
    U->>S: /specworks-test add-short-links
    S->>C: specworks start test --change add-short-links
    C->>F: read specs, design.md, tags, run commands.test
    C-->>S: gate design: [ok]... phase design → test (exit 0)
    S->>F: read specs, design.md Interfaces, existing tests
    S->>F: write tests/test_store.py with @ac tags
    S->>C: specworks gate test --change add-short-links
    C-->>S: [FAIL] every acceptance criterion has a test: AC-LINK-001.3 (exit 1)
    S->>F: add the missing test
    S->>C: specworks gate test --change add-short-links
    C-->>S: gate test: passed (exit 0)
    S-->>U: table of criteria and tests, then "run /specworks-code next"
```

## The skills

`specworks init` (or `specworks skills`) installs the skills in the open
[Agent Skills](https://agentskills.io) format:

| Tool | Installed files | How to run a phase |
|---|---|---|
| Claude Code | `.claude/skills/specworks-*/SKILL.md` | `/specworks-refine`, or just ask ("let's refine ...") |
| GitHub Copilot | `.github/skills/specworks-*/SKILL.md` and `.github/prompts/specworks-*.prompt.md` | `/specworks-refine` in Copilot Chat (agent mode), or just ask |

| Skill | Phase(s) | Goal |
|---|---|---|
| {doc}`../skills/adopt` | — | set specworks up on an existing project; map capabilities; on request, baseline one |
| {doc}`../skills/refine` | refine | understand the problem, compare options → `refinement.md` |
| {doc}`../skills/specify` | specify | proposal, delta specs (REQ/AC), design notes, tasks, traceability |
| {doc}`../skills/design` | design | decide the API with you, record it in `design.md`, create stubs |
| {doc}`../skills/test` | test | failing tests tagged `@ac`, one or more per criterion |
| {doc}`../skills/code` | code | implement task by task, tag `@req`, suite green |
| {doc}`../skills/review` | review | find drift between code, spec and design → `review.md` |
| {doc}`../skills/build` | design → test → code → review | chain the four, in cycles, until the review is clean |
| {doc}`../skills/validate` | validate | read-only PASS/FAIL report |
| {doc}`../skills/close` | close | merge deltas into the living docs, archive the change |

The skills call the CLI from a terminal, so the agent needs terminal access
(Claude Code, Copilot agent mode).

## Text shared by the skills

Two blocks of text are written once, in `src/specworks/skills/_shared/`, and
filled into every skill that marks its place with
`<!-- specworks:include <name> -->` when the skills are installed.

**Running the CLI** (every skill):

```{literalinclude} ../../src/specworks/skills/_shared/running-cli.md
:language: markdown
```

**Picking the change** (every phase skill from specify on):

```{literalinclude} ../../src/specworks/skills/_shared/picking-the-change.md
:language: markdown
```
