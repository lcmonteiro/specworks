**The workflow**: `refine → specify → design → test → code → review → validate → close`,
one skill per phase (`/specworks-<phase>`).

**Selecting the change**: use the change the user named; otherwise the one in
`changes` (`specworks context --json`) that matches the request, or the only
active one; ask when it is ambiguous. When none fits, `/specworks-refine` and
`/specworks-specify` create one; the later phases stop and ask. Use the `ref`
the CLI prints (`module:name`, or `name` at the top level) in every command,
and announce `Using change: <ref>`.

**Running the CLI**: use `specworks <cmd>`. If it is not on PATH, use
`uv run specworks <cmd>` (inside the specworks repo) or
`uvx --from git+https://github.com/lcmonteiro/specworks specworks <cmd>`.
