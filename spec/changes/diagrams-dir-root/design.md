# Design: diagrams-dir-root

## Interfaces

None: `diagrams --dir` keeps its name and type; only how a relative path is resolved changes (`ws.root / dir`, resolved), and a missing folder now fails.
