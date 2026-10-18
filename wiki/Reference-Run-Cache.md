# The run cache

Gates and `specworks validate` reuse the result of a project command already
run on the **same code**: same command and folder, same commit, same
uncommitted and untracked files. The workflow folder (specs, tasks,
`review.md`) does not count, so ticking a task or writing `review.md` does not
re-run the tests. A reused result says so:

```text
$ python -m pytest -q -p no:cacheprovider -o pythonpath=src tests  (in ., exit 0, same code as the run at 2026-10-17 19:56:40)
```

| What | Runs the command |
|---|---|
| `specworks run <key>` | always, and records its result (the latest run on the same code is the one reused) |
| `gate`, `start`, `validate` | only when no result from the same code exists |
| `gate`, `start`, `validate` with `--fresh` | always, once each per invocation, however many gates use it |
| `specworks close` (without `--dry-run`) | always |
| `--no-run` | never (the check becomes a warning) |

- The cache lives in `.git/specworks-runs.json`. Without git, or with
  `SPECWORKS_RUN_CACHE=0`, every run is real.
- Files git ignores (installed dependencies, a local `.env`) and services the
  commands use are not part of the fingerprint: after changing only those, run
  `specworks run <key>` once, or pass `--fresh`. A tracked lockfile change
  already counts.
- Keep files the commands themselves create (`__pycache__/`, `.pytest_cache/`,
  `node_modules/`, build output) in `.gitignore`, or every run changes the
  fingerprint.
- Edits inside git submodules count too; while a submodule holds untracked
  files, nothing is reused.
