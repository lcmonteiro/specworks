# Review: add-inspect-skill

Base: `origin/main`

## Findings

<!-- One line per drift between code, spec and design (API), from `specworks review` and from
reading the diff. `- [ ] R<n>` while open, `- [x] R<n>` once resolved. Write
"None." when there are no findings. -->

- [x] R1 **test-gap** AC-FLOW-016.13, AC-CLI-011.5: the test helpers look for the closing fence as a copy of the opener, language included (tests/workflow/test_findings.py:315 suggestion_block, tests/cli/test_findings.py:92 fenced), but a closing fence takes no language and findings.py _suggestion writes ` ````` as design.md says (test_findings.py:336 itself expects it); 3 tests fail with ValueError
  - **Proposal**: back to test: in both helpers, find the closing fence as the opener without its language (its indentation and backticks only)
  - **Decision**: back to test: look for the closing fence as the opening line without its language (suggestion_block in tests/workflow/test_findings.py, fenced in tests/cli/test_findings.py)
  - done in test: suggestion_block and fenced find the closing fence as the opener without its language; the 3 tests pass
  - confirmed in review: suggestion_block and fenced now look for the closing fence as the opener without its language; AC-FLOW-016.13 and AC-CLI-011.5 tests pass
- [x] R2 **test-gap** AC-SPECS-018.2: tests/specs/test_trace_closed.py:63-64 look for 'src/auth/reset.py:1 (changed since close)' in the text trace, but the matrix writes each location in backticks (`src/auth/reset.py:1` (changed since close), trace.py to_markdown), so the positive assert fails and the two negative ones pass whatever the code does
  - **Proposal**: back to test: assert the marked and the unmarked locations with their backticks
  - **Decision**: back to test: check both the marked and the unmarked locations with the backticks to_markdown puts around them (tests/specs/test_trace_closed.py)
  - done in test: test_trace_closed checks the marked and unmarked locations with their backticks
  - confirmed in review: test_trace_closed asserts the marked location and both unmarked ones with their backticks, and that the unmarked ones are present; it passes
- [x] R3 **quality** specworks-inspect step 1 runs 'specworks cycle --change <ref> --json' for every change, but cycle refuses an archived change (cli/workflow.py:144 require_change; tests/cli/test_archive.py:59), so on a closed change the open I<n> findings routed to inspect (step 3) cannot be listed that way
  - **Proposal**: back to code: in src/specworks/skills/specworks-inspect/SKILL.md step 1, run cycle only for an open change; for a closed one, read its open I<n> findings from inspection.md in the archive folder (the path status gives); then uv run specworks skills
  - **Decision**: back to code: in the specworks-inspect skill run specworks cycle only for an open change; for a closed one read inspection.md in the archive folder; then run uv run specworks skills
  - done in code: specworks-inspect step 1 runs cycle only for an open change; for a closed one it reads the open I<n> lines of inspection.md in the archive folder (status path); installed copy refreshed with specworks skills
  - confirmed in review: specworks-inspect step 1 runs cycle only for an open change and reads open I<n> lines of inspection.md in the archive folder (status path, checked on an archived change) for a closed one; installed copy refreshed
- [x] R4 **quality** tests/workflow/test_build_cycle.py:266 write_inspection writes inspection.md without encoding="utf-8" (CLAUDE.md conventions) and duplicates tests/support/findings.py write_inspection
  - **Proposal**: back to test: use support.findings.write_inspection in test_ac_flow_012_11 and drop the local helper
  - **Decision**: back to test: use support.findings.write_inspection in tests/workflow/test_build_cycle.py and drop the local helper
  - done in test: test_build_cycle uses support.findings.write_inspection; the local helper is gone
  - confirmed in review: test_build_cycle imports support.findings.write_inspection (utf-8); the local helper is gone; AC-FLOW-012.11 passes
- [x] R5 **spec-gap** findings.py:399-400 _suggestion refuses a --lang that is not one word without backticks; neither REQ-FLOW-016 nor REQ-CLI-011 lists that refusal, and no test covers it
  - **Proposal**: accepted: a language with spaces or backticks would break the fence's opening line, so the refusal only guards the fence REQ-FLOW-016 already requires (otherwise back to specify: add the refusal to REQ-FLOW-016 with a scenario)
  - **Decision**: accepted: the --lang refusal only guards the fence REQ-FLOW-016 already requires
- [ ] R6 **spec-gap** REQ-SPECS-018 (specs/specs/spec.md:12-15) says the removed criteria are those left out of the living spec 'as it was at that commit' (the close commit), and 'when that commit cannot be found' none; design.md (agreed with the user) and trace.py:416-427 _specs_at_close compare with the spec at the close commit's parent, since the close commit already holds the merged spec, and report none when that parent or its spec cannot be read. The scenarios AC-SPECS-018.4/.5 and their tests match the code; only the requirement's text says the other commit
  - **Proposal**: back to specify: in REQ-SPECS-018 say 'as it was just before that commit (at its parent)' and 'when that commit or its parent cannot be read, no criterion SHALL be reported as removed'; no design, test or code change
  - **Decision**: back to specify: reword REQ-SPECS-018 to read the living spec just before the close commit (at its parent), and to report none when that commit or its parent cannot be read; only the requirement's text changes
  - done in specify: reworded REQ-SPECS-018: the living spec just before the close commit (at its parent), none when that commit or its parent cannot be read; scenarios unchanged
- [ ] R7 **quality** src/specworks/specs/trace.py:140 living_spec_at's docstring says commit is '(the close commit of the archived change)', but its only caller passes the close commit's parent (trace.py:422) and design.md says it reads the spec at whatever commit it is given
  - **Proposal**: back to code: drop '(the close commit of the archived change)' from the docstring, or say the trace passes the close commit's parent
  - **Decision**: back to code: drop '(the close commit of the archived change)' from living_spec_at's docstring

## Changed files without tags

<!-- Every file `specworks review` lists under untracedSource/untracedTests,
with why it needs no tag (config, refactor, helper of REQ-...) or the
finding that covers it. -->

- `src/specworks/harness/peers/inspect.py`: the `inspect` peer of the new skill; like every other peer module (`validate.py`, ...) it carries no tag, and REQ-HARNESS-001 is tagged on `peers/__init__.py`, which registers it
- `tests/support/findings.py`: test helper (`INSPECTION`, `INSPECTION_ARTIFACT`, `write_inspection`, `read_inspection`) for the tagged AC-FLOW-016.12/016.13, AC-CLI-011.5 and AC-FLOW-018.4 tests
- `tests/test_skills.py`: skill wording tests; the skills have no capability, so they stay untagged (CLAUDE.md)

## Summary

Cycle 1 met the code with 4 failing tests, all on the test side: two helpers expected a closing fence with a language (R1) and a trace test missed the backticks around a location (R2); the inspect skill ran `cycle` on a closed change, which refuses it (R3); one test helper wrote without utf-8 (R4); `--lang` has a refusal no requirement lists (R5, accepted). Cycle 2 carried out R1, R2 and R4 in test and R3 in code, all confirmed and closed here; the suite passes (1202). No spec, design or API change. The check warnings that REQ-CLI-011 and REQ-FLOW-001/010/012/016 were MODIFIED by unify-check-findings after this change started are stale: specify ran after that close, and each MODIFIED block differs from the living spec only by this change's edits.

Reopened for inspection.md I1 (a closed change's trace compared its MODIFIED blocks with today's living spec): the cycle after the reopen added AC-SPECS-018.4/.5 and compared an archived change with the living spec at its close commit's parent; the suite passes (1207) and the trace of unify-check-findings no longer reports removed criteria, so I1 is marked done in review for inspect to confirm. Two open findings: REQ-SPECS-018's text still says the spec "at that commit" while the agreed design and the code use its parent (R6, back to specify), and `living_spec_at`'s docstring names the close commit (R7, back to code).
