# Refinement: clear-decision-prompts

## Problem

When a skill stops for a human decision, the message does not always end with
something the user can simply answer. Some stops end with a clear question
("Merge and archive?"). Others end with an open "ask about…" or "agree on
it", so the user has to work out what is being asked and which answer the
agent expects. The user asked for this in their own words: "Every step that a
human is needed to decide, we should add always in the end a clear option or
options (if more than one give your recommendation) or yes/no".

## Context

**Observed:**
- The packaged skills are in `src/specworks/skills/*/SKILL.md`. Their
  installed copies (`.claude/skills/`, `.github/skills/`,
  `.github/prompts/`) are rendered by `specworks skills`
  (`src/specworks/tools/skills.py`).
- Shared text lives in `src/specworks/skills/_shared/*.md`. A skill pulls it
  in with a line `<!-- specworks:include <name> -->` (`INCLUDE_RE` in
  `tools/skills.py`), and the line is filled in when the skill is rendered.
  `running-cli` is shared this way today.
- These skills stop for a human:
  - adopt: the folder name, the modules, the commands, the context, and the
    capability table;
  - baseline: the capability to baseline, then the requirements and the list
    of suspected bugs;
  - refine: running init, continuing an existing change, the name and module,
    and "Ready to record the refinement?";
  - specify: questions on scope, and the requirements and criteria table;
  - design: the API list ("agree on it");
  - test: confirming the test command;
  - code: "Pause and ask" when a task is unclear, and confirming the test
    command;
  - review: a proposal for each finding ("Then ask");
  - build: "Start cycle N from X?";
  - close: registering a capability, and "Merge and archive?";
  - done: the merge plan, through close.
- Each phase ends with a hand-over sentence ("When you are ready, run
  `/specworks-<next>`"). build, done and specify can lead to more than one
  next step.
- `tests/test_skills.py` renders every packaged skill, so a broken include
  shows up there.

**Assumed:**
- One short shared rule, included in every skill, is enough to shape the
  questions the skills do not spell out.

## Constraints

- [hard] Every stop for a human ends with a closing question in one of two
  forms:
  - a yes/no question;
  - numbered options with exactly one marked "(recommended)" and a one-line
    reason.
- [hard] The end of every phase offers the next step as a choice, with a
  recommendation when there is more than one way on (e.g. `/specworks-build`
  vs `/specworks-design`).
- [hard] Skill text only: no change to the CLI or its behaviour.
- [soft] The rule is written once and included, not repeated in every skill.
- [soft] The installed copies are refreshed with `specworks skills`.

## Options

### Option A: shared rule + fix prompts (chosen)

Add `_shared/asking-the-user.md` with the rule (the two closing forms, one
question at a time, a recommendation always given when there are several
options, and a phase end that offers the next step). Include it in every
skill. Then reword each open decision point listed above, and each phase
end, so that it names its options and its recommended one.

- **Pros:** the rule lives in one place, and the concrete prompts show it in
  use.
- **Cons:** touches nearly every skill.
- **Effort:** M.
- **Touches:** packaged skills (no capability).

### Option B: shared rule only

Include the rule and leave the existing wording as it is.

- **Pros:** the smallest edit.
- **Cons:** the open prompts still read as open and can override the rule
  in practice.
- **Effort:** S.
- **Touches:** packaged skills.

### Option C: inline per prompt

Rewrite each decision point with its own options, without a shared rule.

- **Pros:** precise.
- **Cons:** repeated in many places, and easy to miss in a new skill.
- **Effort:** M.
- **Touches:** packaged skills.

## Recommendation

Option A, chosen by the user, with phase ends included: each phase ends by
offering the next step, e.g. "Next: `/specworks-specify <ref>`
(recommended), or stop here?"

## Open Questions

None blocking. Only skill text changes and no capability holds requirements
for the skills, so the change is likely `skip-specs` (the specify phase
decides).

## Candidate Capabilities

- None: the packaged skills change, and the skills capability is deferred.
