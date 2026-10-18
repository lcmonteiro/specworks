# Proposal: add-link-expiry

## Why

Campaign links must stop working when the campaign ends (open question of add-short-links).

## What Changes

- `shorten(url, ttl=None)` accepts a lifetime in seconds.
- `resolve(code)` rejects an expired code with the new `ExpiredCode`.
- `LinkStore(clock=time.time)` takes a clock, so expiry can be tested.

## Capabilities

### Modified Capabilities

- `links`: REQ-LINK-002 (resolve rejects expired codes) is MODIFIED; REQ-LINK-003 (lifetime) is ADDED.

## Impact

`src/shortlink/store.py`, `src/shortlink/errors.py`. Existing callers are unaffected (defaults).

## Out of Scope

- Changing the lifetime of a URL that already has a code: it keeps its first code and lifetime.
