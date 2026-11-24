# Design: refine-says-when-not-worth-it

## Context

See proposal.md. Text only: `src/specworks/skills/specworks-refine/SKILL.md`,
the refinement instruction in `src/specworks/schema.yaml` (served by
`specworks instructions refinement`), the installed copy under
`.claude/skills/`, and wording tests in `tests/test_skills.py`, which read the
packaged skill with `read_skill` and compare flattened text (`flat`).

## Goals / Non-Goals

- Goal: refine says a request is not a good idea as soon as it finds out,
  with the evidence, and the user decides: go on, reshape or abandon.
- Non-goal: any CLI check of it (gates, `check`, a Verdict section), and the
  other phases.

## Decisions

### The rule in three places of the refine skill

Option A of refinement.md. The stance says what kind of agent refine is, so
a **Candid** bullet goes there, after **Honest about evidence**, which it
extends. Step 3 is where the agent finds out, so the stop and its question go
there, as a paragraph after the list of what to clarify and before "Stop
asking". Step 5 is where the closing options are, so abandoning is offered
there. Alternatives: the rule in the stance only (no concrete stop, the gap
today), or in `_shared/` for every phase (option B, out of scope).

The question has three answers and recommends none by default: which one is
right depends on the objection, and the user decides. The agent marks as
recommended the one the evidence supports, as every other stop does.

`abandon` is named in its real form, `specworks abandon --change "<ref>"
--reason "<why>"` (the CLI requires `--reason`), and runs only on the
user's answer.

### Recording it in refinement.md

The objection and the decision go in **Recommendation**, the section that
already holds the agent's view: `Not recommended: <why>`, then the user's
decision. No new section, so the template and the clearly fine refinements
are unchanged (option C rejected).

### Pinned wording

Stance, a new bullet after **Honest about evidence**:

> - **Candid**: when the evidence says the request is not a good idea, say so plainly, with that evidence; never soften it into one con among many.

Step 3, a new paragraph after the "which option the user prefers" bullet:

> As soon as the evidence says the request itself is not a good idea (it
> duplicates something that exists, breaks a hard constraint, costs more than
> it gives, or fixes the wrong problem), stop and say so before going on:
> "I don't think this is a good idea: <why>", with the evidence. Then ask
> one question, the answer the evidence supports marked (recommended):
> ```
> 1. Go on anyway: refine it as asked, and record the objection
> 2. Reshape the request: <the version that avoids the objection>
> 3. Abandon it: specworks abandon --change "<ref>" --reason "<why>"
> ```
> Never abandon on your own: run `specworks abandon` only when the user
> chooses it, then stop.

Step 5, after the summary sentence:

> While an objection stands (the user went on anyway), add before
> `Stop here`: `Abandon it: specworks abandon --change "<ref>" --reason "<why>"`.

Refinement instruction (`schema.yaml`), the **Recommendation** bullet
becomes:

> - **Recommendation**: The option you recommend and why, in a few lines.
>   Leave it as "Pending" if the user has not agreed yet. When the request
>   itself is not a good idea, write `Not recommended: <why>` and the
>   user's decision (went on anyway, reshaped, or abandoned).

Tests assert these phrases (flattened):
- `**Candid**: when the evidence says the request is not a good idea, say so plainly`
- `"I don't think this is a good idea: <why>"`
- `Never abandon on your own: run \`specworks abandon\` only when the user chooses it`
- `specworks abandon --change "<ref>" --reason "<why>"` in step 3 and in step 5
- `Not recommended: <why>` in the refinement instruction

## Interfaces

None: no CLI, API or data change.

## Diagrams

No structural change.

## Risks / Trade-offs

- An agent may object too readily. Mitigation: the stop needs evidence, and
  "go on anyway" keeps the user in charge.
