# Refinement: remove-stale-skills

## Problem

`specworks init` and `specworks skills` write the packaged skills but never
remove the ones a newer specworks no longer ships. Five skills have been renamed
so far (`sw-refine`, `specworks-propose`, `specworks-interface`,
`specworks-implement`, `specworks-verify`). A project set up with an older
version keeps those copies after a refresh, and an agent can load one, follow
outdated steps and call commands that no longer exist. This was found as
suspected bug 9 of `baseline-integrations`.

## Context

**Observed:**
- `tools/skills.py`, `install_skills`: for each chosen tool, writes
  `<skills_dir>/<name>/SKILL.md` for every packaged skill and, for Copilot,
  `<prompts_dir>/<name>.prompt.md`. It returns the files written, and
  `cli/project.py` (`write_skills`) prints a `skill   <path>` line for each.
- The git history of `src/specworks/skills/` shows the five retired names
  above. Every skill shipped today starts with `specworks-`, which
  `test_skills_are_installed_with_specworks_prefix` asserts.
- The same folders can hold a user's own skills under other names.
- Living spec of `integrations`: REQ-INTEG-005 (Installing the skills) covers
  what is written, but not what happens to what is already there.

**Assumed:**
- Nobody names their own skill `specworks-…`. The prefix is specworks'
  namespace.

## Constraints

- [hard] Never touch a skill or prompt file outside the `specworks-` namespace,
  except the one known pre-prefix name, `sw-refine`.
- [hard] Every removal is visible in the output.
- [soft] Only the chosen tools' folders are cleaned.

## Options

### Option A: Remove stale `specworks-*` copies

On install or refresh, for each chosen tool, delete each `specworks-*` skill
folder and Copilot `specworks-*.prompt.md` that is not shipped any more, plus
`sw-refine`, and print `removed <path>` for each.

- **Pros:** Simple. Cleans every past rename and any future one.
- **Cons:** A user's own `specworks-…` skill would be removed (unlikely).
- **Effort:** S
- **Touches:** `integrations`, `cli` (the output line)

### Option B: A manifest of installed skills

- **Pros:** Never touches a skill specworks didn't write.
- **Cons:** A new file to commit in every project, and today's stale copies
  aren't in any manifest, so they stay.
- **Effort:** M
- **Touches:** `integrations`

### Option C: Report only

- **Pros:** Never deletes anything.
- **Cons:** The stale skills stay until the user acts.
- **Effort:** S
- **Touches:** `integrations`, `cli`

## Recommendation

**Option A**, chosen with the user. The `specworks-` prefix is specworks'
namespace. The five known stale skills disappear on the next
`specworks skills`, and each removal is printed.

## Open Questions

None.

## Candidate Capabilities

- `integrations`: REQ-INTEG-005 MODIFIED, with a new criterion: stale
  `specworks-*` skills and prompts (and `sw-refine`) are removed and reported,
  and other skills are left alone.
