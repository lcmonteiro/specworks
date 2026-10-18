# Refinement: add-short-links

## Problem

Our newsletter tool pastes long tracking URLs into emails; they wrap, break and
look untrustworthy. The team wants "a tiny library that turns a long URL into a
short code and back", usable from the newsletter service.

## Context

**Observed:**
- `src/shortlink/` holds only an empty package; capability `links` is registered
  (prefix LINK) with no living spec yet.
- The project is standard-library only (context).

**Assumed:**
- One process; persistence is not needed for the first version.

## Constraints

- [hard] Standard library only.
- [hard] The same URL must not get two different codes (analytics count per code).
- [soft] Codes short enough to read aloud (6-8 characters).

## Options

### Option A: Random codes in an in-memory store

`LinkStore.shorten(url)` draws a random 6-char base62 code, stores it in a dict.

- **Pros:** simple, codes not guessable in sequence
- **Cons:** needs a reverse map to keep one code per URL
- **Effort:** S
- **Touches:** links

### Option B: Hash of the URL

Code = first 6 chars of base62(sha256(url)).

- **Pros:** deterministic, no reverse map
- **Cons:** collisions must still be handled; code leaks nothing but is fixed forever
- **Effort:** S
- **Touches:** links

## Recommendation

Option A, agreed with the user: a reverse map is trivial and collision handling is simpler.

## Open Questions

- Should codes expire? (who can answer: product owner) - not now; a later change.

## Candidate Capabilities

- `links`: modified - first requirements of the registered capability.
