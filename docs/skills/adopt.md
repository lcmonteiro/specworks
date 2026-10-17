# /specworks-adopt

:Phase: none (set-up)
:Writes: the config; on request, one `baseline-<capability>` change at a time
:Next: `/specworks-refine` for new work; `/specworks-close baseline-<capability>` after a baseline
:Example: {doc}`../tutorial/setup` (stages 1-2)

Bring a project that already has code into specworks, without pretending it
was built with it and without changing any behaviour. Use it when you say
"adopt", "onboard", "baseline a capability", or start using specworks on an
existing (brownfield) project.

```{mermaid}
flowchart TD
    S1["Stage 1: set up<br/>context --json → init<br/>find commands from build files and CI<br/>run test / lint, write context"] --> S2["Stage 2: map capabilities<br/>propose a table → you confirm<br/>capability add ... ; spec list"]
    S2 --> STOP(["stop: ready for /specworks-refine"])
    S2 -.->|on request, one capability| S3["Stage 3: baseline-#lt;capability#gt;<br/>an ordinary change that ADDs<br/>the behaviour the code already has"]
    S3 --> S3a["spec show; run test (must be green)<br/>new baseline-#lt;cap#gt;; phase specify"]
    S3a --> S3b["requirements from tests AND code<br/>suspected bugs → Out of Scope<br/>check; confirm table with you"]
    S3b --> S3c["start design: Interfaces = None<br/>start test: add @ac tags (new test only<br/>for a criterion none covers; it must pass)<br/>start code: add @req tags, nothing else"]
    S3c --> S3d["start review; review --json; review.md<br/>start validate; validate"]
    S3d --> S3e(["hand over to /specworks-close"])
```

**By default it stops after stage 2.** A project is ready for new changes once
its capabilities are mapped; a capability gets a baseline when you ask,
typically the first time a change touches it.

## Stage 1: set up

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 1 | Check the project | `specworks context --json`; `specworks init --dir <dir>` (with your go-ahead) | `root: null` → not set up. Several independent projects → one module each (`specworks module add <path>`) |
| 2 | Find the commands | reads `pyproject.toml`, `package.json`, `Makefile`, `Cargo.toml`, `go.mod`, CI workflows...; then `specworks run test`, `specworks run lint` | a table of `test` / `lint` / `typecheck` / `build` with where each came from; a failing command is the starting state, reported, not fixed |
| 3 | Write the context | reads README, `CLAUDE.md`, `AGENTS.md`, contributing guide | a few lines: what the project is, its stack, conventions a change must follow |
| 4 | Scan globs (when needed) | — | `test_globs` / `source_globs` to skip generated, vendored or fixture code |

## Stage 2: map the capabilities

| # | Step | Command | What it reads from the output |
|---|---|---|---|
| 5 | Propose capabilities | — | a table: capability, path, prefix, description. Grouped by behaviour you would recognise (no `utils` or `models`), a few broad ones. **Stops and waits** for you |
| 6 | Register them | `specworks capability add <name> --path <path> [--prefix <P>] [--description "..."]`; `specworks spec list` | a prefix clash is an error to resolve |
| 7 | Report and stop | — | config, commands (and whether each passes), context, modules, capabilities |

## Stage 3: baseline one capability (on request)

A baseline is an ordinary change named `baseline-<capability>` whose specs
ADD the behaviour the code already has. Its tests and code exist, so the test
and code phases only add tags.

| Phase | In a normal change | In a baseline |
|---|---|---|
| (before) | — | `specworks spec show` (a capability with requirements needs no baseline); `specworks run test` **must be green**, otherwise stop: a red suite cannot show the baseline matches the code |
| specify | requirements for new behaviour | requirements for behaviour the code **already has**, read from existing tests **and** code; `## Purpose` + only ADDED; suspected bugs go to Out of Scope; confirmed with you |
| design | API decided with you, stubs | `## Interfaces` = "None: a baseline records existing behaviour and changes no API." |
| test | failing tests | `@ac` tags on existing tests; a new test only for a criterion none covers, and it must **pass** (if it fails: the criterion is wrong or it is a bug → back to specify) |
| code | implementation | `@req` tags only; any other code change is a review finding |
| review, validate | as usual | the only changed files should be tests and code that gained tags |
| close | as usual | writes the capability's first living spec |

## Guardrails

- One capability per baseline, and only the one asked for.
- Never changes behaviour: no refactors, bug fixes or renames. A failing
  command or a bug is reported, not fixed; it can become its own change.
- You confirm the commands, the capability table and each baseline's
  requirements before they are written.
- Records behaviour the code **has**, not behaviour it should have.
- Never edits living docs by hand.

## Source

````{dropdown} specworks-adopt/SKILL.md
:icon: code

```{literalinclude} ../../src/specworks/skills/specworks-adopt/SKILL.md
:language: markdown
```
````
