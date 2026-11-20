# Review: add-llm-router

Base: `<!-- base branch -->`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **test-gap** router_endpoint's branch for a model with no key or an async key function gives an endpoint with no key, and no test reaches it (src/specworks/harness/router.py:57; REQ-HARNESS-015)
  - **Proposal**: back to test: add a test that router_endpoint of a ChatOpenAI whose api_key is an async function gives an endpoint with no key, so routing falls back to onboard
  - **Decision**: back to test: add a test that router_endpoint of a ChatOpenAI whose api_key is an async function gives an endpoint with no key, so routing falls back to onboard
  - done in test: test_ac_harness_015_1_a_key_the_router_cannot_read_falls_back: an async api_key and a model that is not ChatOpenAI give an endpoint with no key
  - confirmed in review: confirmed: the test reaches router.py's no-key branch; router.py is fully covered
- [x] R2 **quality** the terminal's welcome still says 'Ask one with @<peer> <text>.', which now reads as if a peer must be named (src/specworks/harness/session.py:39; REQ-HARNESS-014)
  - **Proposal**: back to code: welcome 'Peers: ... Ask one with @<peer> <text>, or just type and the best-fitting peer answers.'
  - **Decision**: back to code: welcome 'Peers: ... Ask one with @<peer> <text>, or just type and the best-fitting peer answers.'
  - done in code: the welcome now says: or just type and the best-fitting peer answers (src/specworks/harness/session.py)
  - confirmed in review: confirmed: the welcome says a message without a peer is routed
- [x] R3 **test-gap** the test half removed the second half of the AC-HARNESS-003.3 test, which asserted that a message the user says to nobody runs no peer; REQ-HARNESS-014 now routes it, and AC-HARNESS-003.3's own WHEN/THEN covers only a say addressed to a peer (tests/harness/test_peers.py:201)
  - **Proposal**: accepted: the removed assertion tested the behaviour REQ-HARNESS-014 replaces; AC-HARNESS-014.2/.3 now cover a message to nobody
  - **Decision**: accepted: the removed assertion tested the behaviour REQ-HARNESS-014 replaces; AC-HARNESS-014.2/.3 now cover a message to nobody

## Changed files without tags

None: every changed source and test file carries `@req` or `@ac` tags.

## Summary

Cycle 1 found three findings: R1 (an untested no-key branch of `router_endpoint`) went back to test, R2 (the welcome text) back to code, and R3 (the removed half of the AC-HARNESS-003.3 test) was accepted. Cycle 2 added the test and changed the welcome; both were confirmed here. No spec or design change; the full suite passes (1296) at 96% branch coverage.
