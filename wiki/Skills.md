# Skills

A skill is a `SKILL.md` file that the agent follows: a script in prose with
steps, the `specworks` commands to run at each step, what to do with their
output, the points where it must stop and ask you, and guardrails. Each page
here describes one skill: when it runs, its steps and commands, what it reads
from each output, and its full source.

| Skill | Phase(s) | Writes | Next |
|---|---|---|---|
| [/specworks-adopt](Skills-Adopt) | — | config; on request a `baseline-<capability>` change | `/specworks-refine` |
| [/specworks-refine](Skills-Refine) | refine | `refinement.md` | `/specworks-specify` |
| [/specworks-specify](Skills-Specify) | specify | `proposal.md`, delta specs, `design.md`, `tasks.md`, `traceability.md` | `/specworks-design` |
| [/specworks-design](Skills-Design) | design | Interfaces in `design.md`, stubs | `/specworks-test` |
| [/specworks-test](Skills-Test) | test | tests tagged `@ac` | `/specworks-code` |
| [/specworks-code](Skills-Code) | code | code tagged `@req` | `/specworks-review` |
| [/specworks-review](Skills-Review) | review | `review.md`; small agreed fixes | `/specworks-validate` |
| [/specworks-build](Skills-Build) | design → test → code → review | everything the four phases write | `/specworks-validate` |
| [/specworks-validate](Skills-Validate) | validate | nothing | `/specworks-close` (PASS) or the phase to go back to (FAIL) |
| [/specworks-close](Skills-Close) | close | living docs; config for new capabilities | commit |

Every skill:

- starts with `specworks context --json` and picks the change
  ([You, the skill and the CLI](Concepts-Actors));
- re-reads every artifact from disk before building on it (you may have
  edited it);
- takes paths and IDs from the CLI, never invents them;
- enters its phase with `specworks start <phase>` (from design on), which
  checks the gates before it;
- ends with its gate, a short report, and the next skill to run.
