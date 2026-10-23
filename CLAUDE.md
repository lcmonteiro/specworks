# CLAUDE.md

specworks is a spec-driven development CLI (Python 3.11+, typer, managed with
uv), plus the agent skills it installs. This repo is developed with specworks
itself. `spec.yml` holds the project context, commands and capabilities, and
`spec/changes/active/` holds the work in flight.

## Commands

```bash
uv sync                              # dependencies (pyd2 brings the pinned d2)
uv run specworks <cmd>               # the CLI, from source
uv run pytest                        # tests (specworks run test)
uv run ruff check src tests && uv run mypy   # lint and typecheck (specworks run lint)
uv run coverage run -m pytest && uv run coverage report   # CI fails under 95% branch coverage
```

CI (`.github/workflows/ci.yml`) runs the tests on Ubuntu (Python 3.11-3.14),
Windows and macOS, along with lint, typecheck and a wheel smoke test.

## Layout

| Path | Capability | What |
|---|---|---|
| `src/specworks/core` | `project` | config, workspace and modules, changes and phases, running commands |
| `src/specworks/specs` | `specs` | spec files, checks, tasks, trace, merging deltas at close |
| `src/specworks/workflow` | `workflow` | artifacts, instructions, gates, review, cycles, validate |
| `src/specworks/tools` | `integrations` | D2 diagrams, installing the agent skills |
| `src/specworks/cli` | `cli` | the command surface (`--json`, errors, exit codes) |
| `src/specworks/skills` | (none) | packaged skills; shared text in `_shared/` |
| `src/specworks/templates` | | artifact templates |
| `tests/` | | pytest; `helpers.py` and `samples.py` build sample projects |

Each capability's living docs (`spec.md`, `requirements.md`, `design.md`)
are in `<path>/docs/`.

## How work is done

- Every change goes through the specworks flow, with its skills:
  `/specworks-refine` → `/specworks-specify` → `/specworks-build` →
  `/specworks-done`. Work on one change at a time, and commit and push after
  each step.
- A change with no behaviour change (skill text, docs, tooling) is marked
  `specworks skip-specs`. The skills have no capability yet: how to tag and
  test skill text is still undecided.
- Tests carry `# @ac AC-…` and code carries `# @req REQ-…`. Tags are scanned
  only in `tests/**/*.py` and `src/**/*.py`, so Markdown files are never
  scanned. Never renumber or reuse an ID.
- Never edit the living docs by hand: `specworks close` writes them (the
  close step updates `design.md`).
- During a baseline, a suspected bug is never fixed. Once the user confirms
  it, it becomes its own `fix-<name>` change.

## Conventions

- Read and write text files with `encoding="utf-8"`. Without it, Windows CI
  reads the files as cp1252 and garbles non-ASCII text such as `—`.
- Edit skills in `src/specworks/skills/` only, then run `uv run specworks
  skills` to refresh the installed copies (`.claude/skills/`,
  `.github/skills/`, `.github/prompts/`) and commit them together.
  `tests/test_skills.py` checks some skill wording verbatim.
- Every skill stop for the user ends with one closing question: yes/no, or
  numbered options with one `(recommended)` (`_shared/asking-the-user.md`).
- The CLI's errors are values: `{"error": ...}` with exit 1 under `--json`.
  Paths in output are relative to the workspace root.
- Ruff's line length is 170. Match the surrounding code's comment density and
  naming.
- User-facing documentation lives in the GitHub wiki, not in this repo; the
  README stays short.
