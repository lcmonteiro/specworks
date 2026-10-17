# Proposal: add-short-links

## Why

Long tracking URLs break in newsletter emails. A short code per URL fixes that
(refinement.md, Option A).

## What Changes

- New `LinkStore` with `shorten(url)` and `resolve(code)`.
- New errors `InvalidUrl` and `UnknownCode`.

## Capabilities

### Modified Capabilities

- `links`: first requirements of the registered capability (no living spec yet).

## Impact

New module `src/shortlink/store.py` and `src/shortlink/errors.py`. No dependencies.

## Out of Scope

- Persistence; expiry of codes; custom codes.
