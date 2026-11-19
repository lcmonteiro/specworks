# Tasks: add-llm-router

## 1. The dependency

- [ ] 1.1 Once chatinho's `LLMRouter` accepts `headers` (design.md, Precondition), move the chatinho pin in `pyproject.toml` (the `harness` extra and the dev group) to that commit, add the `openai` extra to both (`chatinho[tui,deepagents,openai]`) and run `uv lock` (REQ-HARNESS-015); verify `uv run python -c "from chatinho.routers import LLMRouter; import inspect; assert 'headers' in inspect.signature(LLMRouter).parameters"` and `specworks run lint`

## 2. Peer descriptions

- [ ] 2.1 Add `skill_description(skill)` and `SkillPeer.description` as stubs in `src/specworks/harness/peers/base.py` (REQ-HARNESS-016); verify `specworks run lint`
- [ ] 2.2 [test] In `tests/harness/`, write failing tests tagged `@ac AC-HARNESS-016.1`: every skill peer of a built session has its packaged skill's front matter `description`, character for character; verify they fail on the stub
- [ ] 2.3 [code] Implement `skill_description` (the front matter `description` of `read_skill`, folded lines joined) and set `self.description` in `SkillPeer.__init__` (REQ-HARNESS-016) tagged `@req REQ-HARNESS-016`; verify `specworks run lint` and that `RefinePeer(model, names).description` starts with the refine skill's description

## 3. The router and its fallback

- [ ] 3.1 Add `src/specworks/harness/router.py` with `FALLBACK`, `HarnessRouter(LLMRouter)` and its `route`, and `router_endpoint(model)`, as stubs (REQ-HARNESS-014, REQ-HARNESS-015); verify `specworks run lint`
- [ ] 3.2 [test] Write failing tests tagged `@ac AC-HARNESS-014.1`, `@ac AC-HARNESS-014.2`, `@ac AC-HARNESS-014.3`, `@ac AC-HARNESS-014.4`, `@ac AC-HARNESS-014.5` and `@ac AC-HARNESS-016.2`, with the router's model answers scripted (no real API): the chosen peer answers; `everyone`, an unknown name, an API error and a timeout go to `onboard` with a warning; `@test`, a reply to `refine` and a hand-over never ask the router's model; the request names every skill peer with its description and the message; verify they fail on the stubs
- [ ] 3.3 [test] Write failing tests tagged `@ac AC-HARNESS-015.1`, `@ac AC-HARNESS-015.2`, `@ac AC-HARNESS-015.3` and `@ac AC-HARNESS-015.4`, recording the routing request's URL, model, `Authorization` and headers: the variables' base URL, model and key; with a stored login the Copilot API base, the session token and `EDITOR_HEADERS`; an expired token renewed before the request; `sk-secret` in no reply, log line or `chat.jsonl` when the routing model fails; verify they fail on the stubs
- [ ] 3.4 [code] Implement `HarnessRouter.route`: `super().route(msg)`, else the id of the peer named `FALLBACK` from `self.peers()`, unless it is the speaker (REQ-HARNESS-014) tagged `@req REQ-HARNESS-014`; verify `specworks run lint`
- [ ] 3.5 [code] Implement `router_endpoint`: the `Endpoint` (model name, base URL, the key as a function: a `SecretStr`'s value, or the model's key function as it is) and the model's `default_headers`; an endpoint with no key for a model that is not a `ChatOpenAI` (REQ-HARNESS-015) tagged `@req REQ-HARNESS-015`; verify `specworks run lint` and that `repr` of the endpoint shows no key
- [ ] 3.6 [code] In `build_harness`, replace `SimpleRouter()` with `HarnessRouter(endpoint, headers=headers)` from `router_endpoint(model)` (REQ-HARNESS-014, REQ-HARNESS-015) tagged `@req REQ-HARNESS-014` and `@req REQ-HARNESS-015`; verify `specworks run lint`

## Workflow follow-up

- The chatinho change (`headers` on `LLMRouter`) is made and merged in chatinho before task 1.1.
