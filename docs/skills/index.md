# Skills

A skill is a `SKILL.md` file that the agent follows: a script in prose with
steps, the `specworks` commands to run at each step, what to do with their
output, the points where it must stop and ask you, and guardrails. Each page
here describes one skill: when it runs, its steps and commands, what it reads
from each output, and its full source.

| Skill | Phase(s) | Writes | Next |
|---|---|---|---|
| {doc}`adopt` | — | config; on request a `baseline-<capability>` change | `/specworks-refine` |
| {doc}`refine` | refine | `refinement.md` | `/specworks-specify` |
| {doc}`specify` | specify | `proposal.md`, delta specs, `design.md`, `tasks.md`, `traceability.md` | `/specworks-design` |
| {doc}`design` | design | Interfaces in `design.md`, stubs | `/specworks-test` |
| {doc}`test` | test | tests tagged `@ac` | `/specworks-code` |
| {doc}`code` | code | code tagged `@req` | `/specworks-review` |
| {doc}`review` | review | `review.md`; small agreed fixes | `/specworks-validate` |
| {doc}`build` | design → test → code → review | everything the four phases write | `/specworks-validate` |
| {doc}`validate` | validate | nothing | `/specworks-close` (PASS) or the phase to go back to (FAIL) |
| {doc}`close` | close | living docs; config for new capabilities | commit |

Every skill:

- starts with `specworks context --json` and picks the change
  ({doc}`../concepts/actors`);
- re-reads every artifact from disk before building on it (you may have
  edited it);
- takes paths and IDs from the CLI, never invents them;
- enters its phase with `specworks start <phase>` (from design on), which
  checks the gates before it;
- ends with its gate, a short report, and the next skill to run.

```{toctree}
:maxdepth: 1

adopt
refine
specify
design
test
code
review
build
validate
close
```
