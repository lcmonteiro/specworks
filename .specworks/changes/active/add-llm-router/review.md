# Review: add-llm-router

Base: `<!-- base branch -->`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **test-gap** router_endpoint's branch for a model with no key or an async key function gives an endpoint with no key, and no test reaches it (src/specworks/harness/router.py:57; REQ-HARNESS-015)
  - **Proposal**: back to test: add a test that router_endpoint of a ChatOpenAI whose api_key is an async function gives an endpoint with no key, so routing falls back to onboard
  - **Decision**: back to test: add a test that router_endpoint of a ChatOpenAI whose api_key is an async function gives an endpoint with no key, so routing falls back to onboard
- [ ] R2 **quality** the terminal's welcome still says 'Ask one with @<peer> <text>.', which now reads as if a peer must be named (src/specworks/harness/session.py:39; REQ-HARNESS-014)
  - **Proposal**: back to code: welcome 'Peers: ... Ask one with @<peer> <text>, or just type and the best-fitting peer answers.'
  - **Decision**: back to code: welcome 'Peers: ... Ask one with @<peer> <text>, or just type and the best-fitting peer answers.'
- [x] R3 **test-gap** the test half removed the second half of the AC-HARNESS-003.3 test, which asserted that a message the user says to nobody runs no peer; REQ-HARNESS-014 now routes it, and AC-HARNESS-003.3's own WHEN/THEN covers only a say addressed to a peer (tests/harness/test_peers.py:201)
  - **Proposal**: accepted: the removed assertion tested the behaviour REQ-HARNESS-014 replaces; AC-HARNESS-014.2/.3 now cover a message to nobody
  - **Decision**: accepted: the removed assertion tested the behaviour REQ-HARNESS-014 replaces; AC-HARNESS-014.2/.3 now cover a message to nobody

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

## Summary

<!-- Two or three lines: what was found, what changed in code, specs and design, and anything sent back to an earlier phase. -->
