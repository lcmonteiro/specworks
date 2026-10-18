# Design: links

## Overview

`LinkStore` keeps two in-memory dicts, `url -> code` and `code -> url`, so a URL
keeps one code and a code resolves in O(1).

![Shorten and resolve](diagrams/shorten-flow.svg)

## Decisions

- **Random base62 codes, 6 characters** (add-short-links): `secrets.choice` over
  `[A-Za-z0-9]`, redrawn on collision. Alternative: hash of the URL; rejected,
  collisions still need handling.
- **URL validation with `urllib.parse`** (add-short-links): scheme `http`/`https`
  and a non-empty `netloc`.

## Interfaces

- `src/shortlink/store.py`: `LinkStore.shorten(url) -> str` raises `InvalidUrl`;
  `LinkStore.resolve(code) -> str` raises `UnknownCode`.
- `src/shortlink/errors.py`: `ShortlinkError` and its subclasses.

## Constraints

- In memory only: the store is lost when the process ends.
