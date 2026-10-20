# Refinement: skill-frontmatter-multiline

## Problem

When specworks installs a skill, it copies the frontmatter one `key: value` line
at a time, so a value written over several lines loses everything after its
first line. Reproduced: a folded `description: >` with two indented lines comes
out of the Copilot copy and the prompt file as `description: >` with no text.
The description is what Copilot reads to decide when to load a skill. This was
found as suspected bug 10 of `baseline-integrations`.

## Context

**Observed:**
- `tools/skills.py`, `split_frontmatter`: keeps only frontmatter lines that
  contain `:`, each as its own (key, line) pair. Continuation lines are dropped,
  and a continuation containing `:` would be taken for a key of its own.
- `render_skill` keeps the pairs whose key the tool understands. `render_prompt`
  takes the `description` pair.
- None of the 12 packaged skills has an indented frontmatter line today, so the
  bug is latent: it bites the first time a long description is written as a
  folded block.
- Living spec of `integrations`: REQ-INTEG-005 (Installing the skills) says each
  tool keeps the frontmatter keys it understands, without saying how a value
  spans lines.

**Assumed:**
- Multi-line values in skill frontmatter use YAML's indented forms (`>`, `|`,
  or plain indented continuation lines).

## Constraints

- [hard] A kept key keeps its whole value, and a dropped key drops its whole
  value.
- [hard] Today's single-line frontmatter is copied byte-for-byte as before, so
  refreshing an installed project changes nothing.

## Options

### Option A: Continuation lines belong to their key

An indented line after a key is part of that key, kept or dropped with it.

- **Pros:** Small. Keeps the text as written. No change for today's skills.
- **Cons:** Covers the indented multi-line forms, not every YAML construct
  (none of which the skills use).
- **Effort:** S
- **Touches:** `integrations`

### Option B: Forbid it with a test

- **Pros:** No production code change.
- **Cons:** A guard, not a fix, and a rule about skill text no capability can
  tag yet.
- **Effort:** S
- **Touches:** none

### Option C: Parse as YAML and write it back

- **Pros:** Handles any YAML.
- **Cons:** Rewrites the quoting and wrapping of every installed skill, which
  gives a noisy diff in every project for no gain today.
- **Effort:** M
- **Touches:** `integrations`

## Recommendation

**Option A**, chosen with the user. It fixes the copy for the multi-line forms
people write, without changing a byte of today's output.

## Open Questions

None.

## Candidate Capabilities

- `integrations`: REQ-INTEG-005 MODIFIED, with a new criterion: a multi-line
  frontmatter value is kept whole (or dropped whole) in every copy.
