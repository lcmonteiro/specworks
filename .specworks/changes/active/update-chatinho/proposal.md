# Proposal: update-chatinho

## Why

The harness extra pins chatinho at `d783cc5`. chatinho `main` is now `57a1b98`,
64 commits ahead: logging to a file (`CHATINHO_LOG_PATH`), lent keys used by the
agent peers, and the endpoint model shared by the connectors and `LLMRouter`.
Moving the pin keeps the harness on the chatinho that is maintained.

## What Changes

- The chatinho pin moves from `d783cc565cf4f5ab2c67385e41bd0d70a1ff0e6b` to
  `57a1b980b075458218b80484b7015ec774224d67`, in both places it is written in
  `pyproject.toml` (the `harness` extra and the `dev` group), and `uv.lock` is
  locked again.
- `tests/harness/test_router.py` patches `AsyncOpenAI` where chatinho now builds
  the router's client (`chatinho.support.kits.model.endpoint`), not
  `chatinho.routers.llm`, which no longer imports it.

A trial run with both changes passes the whole suite (1404 tests), ruff and mypy.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No behaviour of specworks changes, so the change is marked
`specworks skip-specs`.

## Related requirements

- REQ-HARNESS-002 left: the peers are still chatinho deep agent peers; nothing about them changes.
- REQ-HARNESS-006 left: `SpecworksWorktrees` still builds on `GitWorktrees`, whose
  only change in this range is logging around merge and drop.
- REQ-CLI-022 left: the harness command still reports a missing chatinho or deepagents the same way.
- REQ-CLI-023 left: login still imports neither chatinho nor deepagents.

## Impact

- Dependencies: `pyproject.toml` (the pin, twice) and `uv.lock`.
- Tests: one fixture in `tests/harness/test_router.py`.
- No source file under `src/specworks` changes.

## Out of Scope

- Using chatinho's new features in the harness (the log file, the shared endpoint model).
- Moving the harness's `Endpoint` import to `chatinho.support.kits.model`: the old
  path `chatinho.support.parts.keys.endpoint` still exists.
- Replacing the commit pin with a version range: chatinho has no releases.
