# Review: add-inspect-skill

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [ ] R1 **test-gap** AC-FLOW-016.13, AC-CLI-011.5: the test helpers look for the closing fence as a copy of the opener, language included (tests/workflow/test_findings.py:315 suggestion_block, tests/cli/test_findings.py:92 fenced), but a closing fence takes no language and findings.py _suggestion writes ` ````` as design.md says (test_findings.py:336 itself expects it); 3 tests fail with ValueError
  - **Proposal**: back to test: in both helpers, find the closing fence as the opener without its language (its indentation and backticks only)
  - **Decision**: back to test: look for the closing fence as the opening line without its language (suggestion_block in tests/workflow/test_findings.py, fenced in tests/cli/test_findings.py)
  - done in test: suggestion_block and fenced find the closing fence as the opener without its language; the 3 tests pass
- [ ] R2 **test-gap** AC-SPECS-018.2: tests/specs/test_trace_closed.py:63-64 look for 'src/auth/reset.py:1 (changed since close)' in the text trace, but the matrix writes each location in backticks (`src/auth/reset.py:1` (changed since close), trace.py to_markdown), so the positive assert fails and the two negative ones pass whatever the code does
  - **Proposal**: back to test: assert the marked and the unmarked locations with their backticks
  - **Decision**: back to test: check both the marked and the unmarked locations with the backticks to_markdown puts around them (tests/specs/test_trace_closed.py)
  - done in test: test_trace_closed checks the marked and unmarked locations with their backticks
- [ ] R3 **quality** specworks-inspect step 1 runs 'specworks cycle --change <ref> --json' for every change, but cycle refuses an archived change (cli/workflow.py:144 require_change; tests/cli/test_archive.py:59), so on a closed change the open I<n> findings routed to inspect (step 3) cannot be listed that way
  - **Proposal**: back to code: in src/specworks/skills/specworks-inspect/SKILL.md step 1, run cycle only for an open change; for a closed one, read its open I<n> findings from inspection.md in the archive folder (the path status gives); then uv run specworks skills
  - **Decision**: back to code: in the specworks-inspect skill run specworks cycle only for an open change; for a closed one read inspection.md in the archive folder; then run uv run specworks skills
- [ ] R4 **quality** tests/workflow/test_build_cycle.py:266 write_inspection writes inspection.md without encoding="utf-8" (CLAUDE.md conventions) and duplicates tests/support/findings.py write_inspection
  - **Proposal**: back to test: use support.findings.write_inspection in test_ac_flow_012_11 and drop the local helper
  - **Decision**: back to test: use support.findings.write_inspection in tests/workflow/test_build_cycle.py and drop the local helper
  - done in test: test_build_cycle uses support.findings.write_inspection; the local helper is gone
- [x] R5 **spec-gap** findings.py:399-400 _suggestion refuses a --lang that is not one word without backticks; neither REQ-FLOW-016 nor REQ-CLI-011 lists that refusal, and no test covers it
  - **Proposal**: accepted: a language with spaces or backticks would break the fence's opening line, so the refusal only guards the fence REQ-FLOW-016 already requires (otherwise back to specify: add the refusal to REQ-FLOW-016 with a scenario)
  - **Decision**: accepted: the --lang refusal only guards the fence REQ-FLOW-016 already requires

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

- `src/specworks/harness/peers/inspect.py`: the `inspect` peer of the new skill; like every other peer module (`validate.py`, ...) it carries no tag, and REQ-HARNESS-001 is tagged on `peers/__init__.py`, which registers it
- `tests/support/findings.py`: test helper (`INSPECTION`, `INSPECTION_ARTIFACT`, `write_inspection`, `read_inspection`) for the tagged AC-FLOW-016.12/016.13, AC-CLI-011.5 and AC-FLOW-018.4 tests
- `tests/test_skills.py`: skill wording tests; the skills have no capability, so they stay untagged (CLAUDE.md)

## Summary

The suite meets the code with 4 failing tests (1198 pass), all on the test side: two helpers expect a closing fence with a language (R1) and a trace test misses the backticks around a location (R2). The inspect skill runs `cycle` on a closed change, which refuses it (R3); one test helper writes without utf-8 (R4); `--lang` has a refusal no requirement lists (R5, proposed accepted). Nothing changed here (build: proposed, not fixed): R1, R2 and R4 go back to test, R3 to code. The check warnings that REQ-CLI-011 and REQ-FLOW-001/010/012/016 were MODIFIED by unify-check-findings after this change started are stale: specify ran after that close, and each MODIFIED block differs from the living spec only by this change's edits.
