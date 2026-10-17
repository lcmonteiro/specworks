# What `start` checks

`specworks start <phase>` runs the gates the move depends on, in order, and
moves the change only if they all pass. It stops at the first gate that fails;
the change stays where it was (exit 1).

- **Moving forward**: every phase left behind must pass its gate.
- **Going back or re-entering**: only the gate of the phase just before the
  target.
- Phases without a gate (`refine`) are skipped. `done` cannot be started:
  `specworks close` finishes a change.

| From → to | Gates run | Why |
|---|---|---|
| refine → specify | none | refine has no gate |
| specify → design | specify | forward one phase |
| specify → test | specify, design | forward: every phase left behind |
| refine → code | specify, design, test | forward |
| design → design | specify | re-enter: the gate before it (accepts edited specs) |
| review → test | design | back: the gate before the target |
| review → design | specify | back |
| code → specify | none | back: refine has no gate |
| review → validate | review | forward |
| validate → close | validate | forward |

When `gate specify` passes during a `start`, the change records each
requirement's fingerprint (`specified` in `.change.yaml`); the later gates
warn about every requirement changed, added or dropped since then.

The gates reuse a project command's result from the same code; with `--fresh`,
each command runs for real once per `start`, however many gates use it.

The logic is `gates_to_start` in {doc}`../api/workflow`.
