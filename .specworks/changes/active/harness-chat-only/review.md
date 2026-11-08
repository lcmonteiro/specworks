# Review: harness-chat-only

Base: `add-chatinho-harness` (28dd005; this change is stacked on it, `origin/main` does not have it yet)

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **quality** REQ-HARNESS-009: signature() leaves out only chat.jsonl, but with telemetry on every change command appends events.jsonl (and events.sent) to the change folder, read-only ones included (gate, validate, cycle, run); a peer that only checks another active change makes that change the run's, the very case design.md rejected naming for (src/specworks/harness/backend.py:62, src/specworks/cli/telemetry.py:26)
  - **Proposal**: back to design: signature(folder) also leaves out the telemetry log, events.jsonl and events.sent (core.events EVENTS_FILE, SENT_FILE), so only a peer's own work on a change binds it; Interfaces and the Decision updated, a test that a recorded event alone does not bind a change, the code follows
  - **Decision**: back to design: signature() also ignores events.jsonl and events.sent, with a test that a recorded event alone does not bind a change
  - done in design: signature() in design.md Interfaces and Decision now also leaves out events.jsonl and events.sent; test and code follow
  - done in implement: signature() also leaves out events.jsonl and events.sent (IGNORED in backend.py), so a recorded event alone does not bind a change
  - confirmed in review: confirmed in cycle 2: IGNORED in backend.py:19 leaves out chat.jsonl, events.jsonl and events.sent, as design.md says; test_a_recorded_event_alone_does_not_bind_a_change and the two signature tests in tests/harness/test_backend.py pass (the .gitignore a first event creates is R4)
- [x] R2 **design-gap** design.md says from_line stays for reading a log in tests, but no test or code reads through it since load() went: it is dead code (src/specworks/harness/backend.py:40; design.md Decision 'The run's change is the first active change whose folder changes')
  - **Proposal**: back to design: drop from_line, its only reader (load) is gone; remove the sentence that keeps it and list it under Removed in Interfaces; the code half deletes it
  - **Decision**: back to design: remove the unused from_line from the design and the code
  - done in design: from_line() listed as removed under Interfaces and the Decision no longer keeps it; the code half deletes it
  - done in implement: from_line() removed from backend.py with its unused MessageID import
  - confirmed in review: confirmed in cycle 2: from_line() and its MessageID import are gone from backend.py, design.md lists it under Removed; nothing referred to it
- [x] R3 **quality** AC-HARNESS-007.5: a run now has no change until a peer writes in a change folder, so on a run that continues a change (no --change any more) /merge test is refused first, and the refusal says 'create it before merging a workspace', wrong for a change that already exists and silent on how to go on (src/specworks/harness/workspaces.py:162)
  - **Proposal**: back to code: the refusal says how the run gets its change, e.g. 'the run has no change yet: ask the peer working on it to go on (such as @build go on with <change>), then merge'; still an error saying the run has no change, as AC-HARNESS-007.5 asks. Alternative, larger: back to specify: with no change yet, /merge takes the change whose folder the worktree's branch changed
  - **Decision**: back to design: when the run has no change yet, /merge's refusal says to ask the peer working on the change to go on first (so the run binds it), not to create one; code follows
  - done in design: design.md has a new Decision and an Interfaces entry giving /merge's no-change refusal text (ask the peer to go on with the change, then merge); the code half changes the text
  - done in implement: MergeCommand's no-change refusal now reads the design.md text: ask the peer working on the change to go on with it (such as @build go on with <change>), then merge
  - confirmed in review: confirmed in cycle 2: MergeCommand's no-change refusal (workspaces.py:162) reads the design.md text word for word; test_ac_harness_007_5_no_change_yet asserts it and that it no longer says create
- [ ] R4 **quality** REQ-HARNESS-009 (after R1): signature() still counts the change folder's .gitignore, and record_event writes it (ensure_ignored adds events.jsonl and events.sent) the first time a change logs an event; telemetry is opt-in, so on a change that has logged no event yet (made before telemetry was turned on, or by hand) a peer's read-only check (gate, validate, cycle, run) creates .gitignore and binds that change, the case R1 closed; the R1 test logs an event before the run, so .gitignore already exists and hides it (src/specworks/harness/backend.py:19, src/specworks/core/events.py:35; tests/harness/test_backend.py test_a_recorded_event_alone_does_not_bind_a_change)
  - **Proposal**: back to design: signature(folder) also leaves out .gitignore (core.events IGNORE_FILE), which only ensure_ignored writes as a side effect of a log, never a peer's work on the change; Interfaces and the Decision updated, a test that a first recorded event on a change with no .gitignore does not bind it, the code adds IGNORE_FILE to IGNORED. Alternative: accepted: telemetry is opt-in and a change created with it on already has its .gitignore
  - **Decision**: back to design: signature() also ignores .gitignore (core.events IGNORE_FILE), with a test that a first recorded event on a change with no .gitignore does not bind it; the code follows
  - done in design: signature() in design.md Interfaces and Decision now also leaves out .gitignore (core.events IGNORE_FILE), and its docstring says so; the test (a first recorded event on a change with no .gitignore does not bind it) and the code (IGNORE_FILE in IGNORED) follow

## Changed files without tags

- `tests/harness/scripted.py`: test helper (the scripted model and user, `chat(say=, to=)`, `touches`) for the REQ-HARNESS-009 and REQ-CLI-022 tests; no behaviour of its own.
- `tests/harness/conftest.py`: untouched by this change (listed only against `origin/main`); skips the folder without the harness extra and builds the sample project, no behaviour of its own.
- `src/specworks/harness/__init__.py`: untouched by this change (listed only against `origin/main`); re-exports `build_harness`, `run_harness`, `model_from_env`, `ModelSettingsError`, plumbing for REQ-CLI-022.

## Summary

Cycle 2: the suite passes (1068 passed, 4 skipped on Python 3.11, where the harness tests are skipped; tests/harness and tests/cli/test_harness.py, 62 passed on 3.13 with the extra). R1, R2 and R3 were carried out as decided and are closed: the signature leaves out the telemetry log, `from_line` is gone, and `/merge`'s no-change refusal says to ask the peer to go on. One new finding, open for the next cycle: R4 (a first telemetry event creates the change's `.gitignore`, which still binds the change), proposed back to design. No spec, design or code changed in review. The criteria dropped on purpose (AC-CLI-022.3, .4, AC-HARNESS-009.3) are the warnings `specworks check` gives.
