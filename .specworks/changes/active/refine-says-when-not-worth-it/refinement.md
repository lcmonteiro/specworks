# Refinement: refine-says-when-not-worth-it

## Problem

When exploring a request in the refine phase shows that the request itself is
not a good idea (it duplicates something that exists, breaks a constraint,
costs more than it gives, or fixes the wrong problem), the refine skill gives
the agent no place to say so. Its stance ("curious, not prescriptive", "do not
decide for them on product questions") leads every path to options for the
request and on to specify, so the objection gets softened into one con among
many, and the user spends a whole specify/build on it before anyone says it.

## Outcomes

- As soon as the agent finds out a request is not a good idea, it stops and
  says so plainly with the evidence ("I don't think this is a good idea:
  <why>"), then asks one question: go on anyway, reshape the request, or
  abandon it (`specworks abandon <ref>`).
- The decision stays the user's: the agent never abandons on its own, and a
  request the user goes on with is refined as usual.
- When the user goes on anyway, `refinement.md` records the objection and the
  user's decision, and the end of the phase offers abandoning while the
  objection stands.

## Context

**Observed:**
- `src/specworks/skills/specworks-refine/SKILL.md`: the stance (curious,
  grounded, honest about evidence, no premature solution), step 3 Explore
  (problem → outcomes → scope → constraints → 2-3 options → preference) and
  step 5, which offers only `/specworks-specify` or "Stop here".
- `src/specworks/schema.yaml`, the refinement instruction: "Include 'do nothing
  / minimal' when it is a real option"; the Recommendation is an option or
  "Pending".
- `specworks abandon` archives a change without merging its specs; only
  `specworks-baseline` mentions it today.
- `tests/test_skills.py` pins some skill wording verbatim.

**Assumed:**
- The instruction text in `schema.yaml` is packaged guidance like the skills,
  not behaviour with a requirement, so the change can be `skip-specs`.

## Constraints

- [hard] The decision stays the user's: the agent objects, it never abandons.
- [hard] Skills are edited in `src/specworks/skills/` only, refreshed with
  `specworks skills` and committed together; pinned wording in
  `tests/test_skills.py` stays in sync.
- [hard] Every stop ends with one closing question (`_shared/asking-the-user.md`).
- [soft] No CLI behaviour change, so the change is `skip-specs`.

## Options

### Option A: refine skill and refinement instruction

A **Candid** stance bullet; in step 3 an explicit stop as soon as the evidence
says the request is not a good idea, with three answers (go on anyway, reshape
it, abandon with `specworks abandon <ref>`); the refinement instruction lets the
Recommendation read "Not recommended: <why>" with the user's decision; step 5
offers abandoning while the objection stands.

- **Pros:** smallest change that meets every outcome; stays in refine.
- **Cons:** other phases still have no such rule.
- **Effort:** S
- **Touches:** the refine skill, `schema.yaml` (no capability)
- **Outcomes:** meets all three.

### Option B: A, plus a shared rule for every phase

The rule in `_shared/`, included by every skill.

- **Pros:** specify, design and review could object too.
- **Cons:** beyond the agreed scope; touches about nine skills.
- **Effort:** M
- **Touches:** every skill
- **Outcomes:** meets all three, and more.

### Option C: A, plus a Verdict section a gate checks

`## Verdict` in the template, and the refine gate refuses an empty one.

- **Pros:** enforced, not only asked for.
- **Cons:** a CLI change that needs specs; ceremony on every refinement,
  including the clearly fine ones.
- **Effort:** M/L
- **Touches:** `workflow` (gates, template)
- **Outcomes:** meets all three.

## Recommendation

Option A, agreed with the user: the smallest change that meets the outcomes,
kept to the refine phase.

## Open Questions

- None blocking. Whether other phases should object the same way is a later
  change (who can answer: the user).

## Candidate Capabilities

- None: skill text and the refinement instruction only (`skip-specs`).
