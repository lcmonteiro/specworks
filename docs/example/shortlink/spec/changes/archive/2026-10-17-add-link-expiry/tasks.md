# Tasks: add-link-expiry

## 1. Expiry

- [x] 1.1 Extend `LinkStore(clock)`, `shorten(url, ttl)` and add `ExpiredCode` as stubs (REQ-LINK-003, REQ-LINK-002); verify the existing tests pass
- [x] 1.2 Write failing tests for AC-LINK-003.1, AC-LINK-003.2, AC-LINK-002.3 tagged `@ac`; verify they fail on the stub
- [x] 1.3 Implement lifetimes (REQ-LINK-003) and expiry in `resolve` (REQ-LINK-002) tagged `@req`; verify the 1.2 tests pass
