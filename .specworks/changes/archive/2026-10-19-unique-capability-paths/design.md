# Design: unique-capability-paths

## Interfaces

None: the checks are internal. `load_workspace` raises its existing
`ConfigError`, and `specworks capability add` reports it through the existing
error output.
