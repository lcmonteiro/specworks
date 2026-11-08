# Review: harness-chat-only

Base: `add-chatinho-harness` (28dd005; this change is stacked on it, `origin/main` does not have it yet)

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **quality** REQ-HARNESS-009: signature() leaves out only chat.jsonl, but with telemetry on every change command appends events.jsonl (and events.sent) to the change folder, read-only ones included (gate, validate, cycle, run); a peer that only checks another active change makes that change the run's, the very case design.md rejected naming for (src/specworks/harness/backend.py:62, src/specworks/cli/telemetry.py:26)
  - **Proposal**: back to design: signature(folder) also leaves out the telemetry log, events.jsonl and events.sent (core.events EVENTS_FILE, SENT_FILE), so only a peer's own work on a change binds it; Interfaces and the Decision updated, a test that a recorded event alone does not bind a change, the code follows
  - **Decision**: back to design: signature() also ignores events.jsonl and events.sent, with a test that a recorded event alone does not bind a change
- [ ] R2 **design-gap** design.md says from_line stays for reading a log in tests, but no test or code reads through it since load() went: it is dead code (src/specworks/harness/backend.py:40; design.md Decision 'The run's change is the first active change whose folder changes')
  - **Proposal**: back to design: drop from_line, its only reader (load) is gone; remove the sentence that keeps it and list it under Removed in Interfaces; the code half deletes it
  - **Decision**: back to design: remove the unused from_line from the design and the code
- [ ] R3 **quality** AC-HARNESS-007.5: a run now has no change until a peer writes in a change folder, so on a run that continues a change (no --change any more) /merge test is refused first, and the refusal says 'create it before merging a workspace', wrong for a change that already exists and silent on how to go on (src/specworks/harness/workspaces.py:162)
  - **Proposal**: back to code: the refusal says how the run gets its change, e.g. 'the run has no change yet: ask the peer working on it to go on (such as @build go on with <change>), then merge'; still an error saying the run has no change, as AC-HARNESS-007.5 asks. Alternative, larger: back to specify: with no change yet, /merge takes the change whose folder the worktree's branch changed
  - **Decision**: back to design: when the run has no change yet, /merge's refusal says to ask the peer working on the change to go on first (so the run binds it), not to create one; code follows

## Changed files without tags

- `tests/harness/scripted.py`: test helper (the scripted model and user, `chat(say=, to=)`, `touches`) for the REQ-HARNESS-009 and REQ-CLI-022 tests; no behaviour of its own.
- `tests/harness/conftest.py`: untouched by this change (listed only against `origin/main`); skips the folder without the harness extra and builds the sample project, no behaviour of its own.
- `src/specworks/harness/__init__.py`: untouched by this change (listed only against `origin/main`); re-exports `build_harness`, `run_harness`, `model_from_env`, `ModelSettingsError`, plumbing for REQ-CLI-022.

## Summary

The suite passes (1068 passed on Python 3.11, where the harness tests are skipped; tests/harness and tests/cli/test_harness.py, 59 passed on 3.13 with the extra; branch coverage 97%). Every requirement has code and every criterion a test that checks its THEN; the code matches the agreed Interfaces. Three findings, all open for the next cycle: R1 (the telemetry log binds a change a peer only checks) and R2 (dead `from_line`) back to design, R3 (the merge refusal on a continued run) back to code. No spec, design or code changed in review. The criteria dropped on purpose (AC-CLI-022.3, .4, AC-HARNESS-009.3) are the warnings `specworks check` gives.
