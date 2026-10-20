# Refinement: run-unknown-key

## Problem

`specworks run <key>` with a key that is not a command key gives advice that
breaks the project. Reproduced: `specworks run frobnicate` says
`no 'frobnicate' command configured; add it under commands: in spec.yml (e.g.
test: uv run pytest)`, but `commands:` accepts only `test`, `lint`,
`typecheck`, `build` and `format`, so following it makes every command fail
with "unknown keys". The example also always shows `test`, whatever key was
asked for. Found as suspected bug 12 of `baseline-cli`.

## Context

**Observed:**
- `core/runner.py`, `run_command`: looks the key up in the merged commands and
  raises `CommandError("no '<key>' command configured; ...")` when it is
  missing, whatever the key.
- `core/config.py`: `COMMAND_KEYS = ("test", "lint", "typecheck", "build",
  "format")`; `load_commands` refuses any other key.
- Callers: `cli/workflow.py` `run` (any key the user types) and
  `workflow/checks.py` (the gates, known keys only), both through `cached_run`.
- Living spec: `project` REQ-PROJ-013 (running the project's commands).

**Assumed:**
- Nobody relies on the current wording for an unknown key.

## Constraints

- [hard] The message never suggests a config that doesn't load.
- [hard] Errors stay `SpecworksError`s, so `--json` gets an error object and
  exit 1, like every other error.
- [soft] A known but unconfigured key keeps today's message, with an example
  for that key.

## Options

### Option A: Refuse an unknown key

`run_command` refuses a key outside `COMMAND_KEYS`, listing the valid ones. An
unconfigured known key keeps its message, with the example using that key.

- **Pros:** Small, one place, the gates and `run` agree, `--json` keeps working.
- **Cons:** `--help` still lists the keys only in the argument's help text.
- **Effort:** S
- **Touches:** `project`

### Option B: A plus a fixed choice on the CLI

- **Pros:** `--help` shows the choices.
- **Cons:** The CLI framework's error has exit 2 and no `--json` object.
- **Effort:** S
- **Touches:** `project`, `cli`

### Option C: Allow custom keys

- **Pros:** The current message becomes true; `run e2e` works.
- **Cons:** A new feature, not a fix; the gates still use only the five keys.
- **Effort:** M
- **Touches:** `project`, `cli`

## Recommendation

**Option A**, chosen with the user.

## Open Questions

None.

## Candidate Capabilities

- `project`: REQ-PROJ-013 MODIFIED. An unknown key is refused naming the valid
  keys; the unconfigured message's example uses the key asked for.
