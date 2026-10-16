**Picking the change**: start with `specworks context --json`.
- `"root": null` means the project is not set up: stop and ask whether to run
  `specworks init`. Never create its files by hand.
- `context` is the project's constraints, already merged top level → module.
  Apply it; never copy it into an artifact.
- Use the change the user named; otherwise the one in `changes` that matches
  the request (`--all` lists every module's). Ask when more than one could fit.
  Announce `Using change: <ref>` and pass that `ref` (`module:name` for another
  module) to every command.
- Re-read every artifact from disk before relying on it: the user may have
  edited it.
