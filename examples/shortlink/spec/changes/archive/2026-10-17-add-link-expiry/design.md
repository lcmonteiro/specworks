# Design: add-link-expiry

## Decisions

### Injected clock

`LinkStore(clock=time.time)`: tests pass a fake clock instead of sleeping. Serves: REQ-LINK-003, REQ-LINK-002.

## Interfaces

- `src/shortlink/store.py`: `LinkStore(clock: Callable[[], float] = time.time)` (extended, REQ-LINK-003)
- `src/shortlink/store.py`: `LinkStore.shorten(url: str, ttl: float | None = None) -> str`, raises `ValueError` when `ttl <= 0` (extended, REQ-LINK-003)
- `src/shortlink/store.py`: `LinkStore.resolve(code: str) -> str`, also raises `ExpiredCode` (extended, REQ-LINK-002)
- `src/shortlink/errors.py`: `ExpiredCode(ShortlinkError)` (new)
