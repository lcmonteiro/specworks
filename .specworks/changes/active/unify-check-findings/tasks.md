# Tasks: unify-check-findings

## 1. Check artifacts in the schema

- [x] 1.1 Add `findings: {letter: R, blocks: [review, validate]}` to `review` and the optional `validation` artifact (`validation.md`, phase `validate`, `requires: [review]`, `findings: {letter: V, blocks: [validate]}`) to `schema.yaml`, `templates/validation.md`, and `Artifact.findings`, `CheckArtifact`, `check_artifacts()`, `check_artifact(id)`, `check_artifact_for(finding_id)` in `artifacts.py` as stubs per design.md Interfaces (REQ-FLOW-018, REQ-FLOW-001); verify `uv run ruff check src tests && uv run mypy`
- [ ] 1.2 [test] Write failing tests for the declared check artifacts and for validation's status, ready and optional, then done, tagged `@ac AC-FLOW-018.1`, `@ac AC-FLOW-001.5`; keep AC-FLOW-001.1 to 001.4 passing; verify the new ones fail on the stubs
- [x] 1.3 [code] Implement the check artifacts read from the schema (letters unique, `WorkflowError` naming them for an unknown id or letter) (REQ-FLOW-018, REQ-FLOW-001) tagged `@req REQ-FLOW-018`, `@req REQ-FLOW-001`; verify by typecheck and `uv run specworks status --change unify-check-findings` listing validation

## 2. Findings of any check artifact

- [x] 2.1 Create `workflow/findings.py` by moving the parser, routing, `Finding`, `ReviewDoc` (as `FindingsDoc`), `FindingError` and the writers out of `review.py`, with `parse_findings(text, artifact)`, `read_findings`, `read_all_findings`, the `artifact` and `check` parameters of `add_finding` and `Finding.check` as stubs per design.md Interfaces; update every import in `src` and `tests` (REQ-FLOW-010, REQ-FLOW-016); verify `uv run ruff check src tests && uv run mypy`
- [ ] 2.2 [test] Write failing tests for a `V` finding read from validation.md, a letter from another artifact reported as unreadable, `back to review:` (with `back to review only:` not a route), and `done in review:` routing on to validate, tagged `@ac AC-FLOW-018.2`, `@ac AC-FLOW-018.3`, `@ac AC-FLOW-010.10`, `@ac AC-FLOW-010.11`; keep AC-FLOW-010.1 to 010.9 passing; verify the new ones fail on the stubs
- [ ] 2.3 [test] Write failing tests for adding a finding to validation (created from its template, V1, routed, `done in code:` by its ID, review.md unchanged) for an unknown check artifact or ID, and for `done in review:` written under a V finding, tagged `@ac AC-FLOW-016.9`, `@ac AC-FLOW-016.10`, `@ac AC-FLOW-016.11`; keep AC-FLOW-016.1 to 016.8 passing; verify the new ones fail on the stubs
- [x] 2.4 [code] Implement the reader per check artifact (its letter in `FINDING_RE`, other letters unreadable, `review` as a `back to`, decision and `done in` step, `done in review:` routing to validate) and the writers to the artifact asked for or named by the ID's letter, `close_finding` writing `confirmed in <artifact phase>:`, the `**Check**` line (REQ-FLOW-010, REQ-FLOW-016, REQ-FLOW-018) tagged `@req REQ-FLOW-010`, `@req REQ-FLOW-016`; verify by typecheck and adding then closing a V finding on a scratch change with `uv run python -c ...`

## 3. Gates and cycles over every check artifact

- [x] 3.1 Add `artifact_readable(artifact)`, `artifact_closed(artifact)`, `GateContext.findings(artifact)` in `checks.py` and `next` in `next_cycle` as stubs, replacing `review_readable` and `review_closed` in the review gate and validate rows (REQ-FLOW-011, REQ-FLOW-012, REQ-FLOW-013); verify `uv run ruff check src tests && uv run mypy`
- [ ] 3.2 [test] Write failing tests that an open V1 neither blocks nor warns in the review gate, and that validate and `gate validate` fail on an open V1 naming `/specworks-validate` and pass once it is ticked, tagged `@ac AC-FLOW-011.9`, `@ac AC-FLOW-013.10`; keep AC-FLOW-011.1 to 011.8 and AC-FLOW-013.1, 013.3 to 013.9 passing; verify the new ones fail on the stubs
- [ ] 3.3 [test] Write failing tests for a cycle from an open `test-gap` V1 (implement, test, review, V1 listed) for the next state (implement, validate, close), and for a finding waiting for validate (no cycle, next validate), tagged `@ac AC-FLOW-012.8`, `@ac AC-FLOW-012.9`, `@ac AC-FLOW-012.10`; keep AC-FLOW-012.1 to 012.7 passing; verify the new ones fail on the stubs
- [x] 3.4 [code] Implement the readability and open-findings checks per check artifact in the gates that each one blocks, `next_cycle` over `read_all_findings` with `next`, findings routed to validate starting no cycle (REQ-FLOW-011, REQ-FLOW-012, REQ-FLOW-013) tagged `@req REQ-FLOW-011`, `@req REQ-FLOW-012`, `@req REQ-FLOW-013`; verify by typecheck and `uv run specworks cycle --change unify-check-findings --json` showing `next`

## 4. Validate writes validation.md

- [x] 4.1 Add `write_validation(ctx)` in `validate.py` and `--write` on `specworks validate` as stubs (REQ-FLOW-019, REQ-CLI-023); verify `uv run ruff check src tests && uv run mypy`
- [ ] 4.2 [test] Write failing tests for a failed validate (V1 → code, V2 → test, each with its `**Check**` line, Summary FAIL), a passing one (`None.`, Summary PASS with the groups), a rerun after a fix (V1 confirmed, V2 not repeated, a hand-written V3 and every other line unchanged), warnings only in the Summary, and a check review fixes routed to review, tagged `@ac AC-FLOW-019.1` to `@ac AC-FLOW-019.5`, with the pinned wording of design.md; verify they fail on the stubs
- [ ] 4.3 [test] Write failing CLI tests for `validate --write` on FAIL (exit 1, the path, a finding routed to code) and on PASS (exit 0, `None.`), and that validate without `--write` creates no validation.md, tagged `@ac AC-CLI-023.1`, `@ac AC-CLI-023.2`, `@ac AC-CLI-023.3`; update AC-FLOW-013.2 to validate without `--write`, tagged `@ac AC-FLOW-013.2`; verify the new ones fail on the stubs
- [x] 4.4 [code] Implement `write_validation` as design.md's five steps, through the finding writers, and `validate --write` printing the path (REQ-FLOW-019, REQ-CLI-023, REQ-FLOW-013) tagged `@req REQ-FLOW-019`, `@req REQ-CLI-023`; verify by typecheck and `uv run specworks validate --write --change unify-check-findings --no-run` writing a readable validation.md

## 5. The finding command

- [x] 5.1 Add `--artifact` to `specworks finding add` as a stub (REQ-CLI-011); verify `uv run specworks finding add --help`
- [ ] 5.2 [test] Write failing CLI tests for a finding added to and closed in validation.md (V1, validation.md's path, no review.md created) and an unknown artifact refused naming the check artifacts, tagged `@ac AC-CLI-011.3`, `@ac AC-CLI-011.4`; keep AC-CLI-011.1 and 011.2 passing; verify the new ones fail on the stub
- [x] 5.3 [code] Implement `--artifact` (default `review`), the path of the artifact each command wrote, and `next` printed by `specworks cycle` (REQ-CLI-011, REQ-FLOW-012) tagged `@req REQ-CLI-011`; verify by `uv run specworks finding add --help` and typecheck

## 6. Skills

- [x] 6.1 [code] `specworks-validate`: write validation.md with `specworks validate --write`, add its own findings with `specworks finding add ... --artifact validation`, close its own once fixed, commit after the verdict, and on FAIL offer the phase of the earliest open finding; update `tests/test_skills.py` (validate is no longer read-only and now commits) (REQ-FLOW-019); verify `uv run specworks skills` and `uv run pytest tests/test_skills.py`
- [x] 6.2 [code] `_shared/back-from-review.md`, `specworks-review`, `specworks-build` and `specworks-reopen`: findings of every check artifact (`specworks finding done <ID>`, `R<n>` or `V<n>`), review closing only its `R` findings and marking each `V` finding it checked `done in review:`, `back to review:` as a route, `next` from `specworks cycle` (REQ-FLOW-010, REQ-FLOW-012); verify `uv run specworks skills` and `uv run pytest tests/test_skills.py`

## Workflow follow-up

- The living workflow design (module list, "review.md is parsed strictly", "review.md is written by commands that read their edit back", Interfaces, the Constraints line "Validate and the gates write nothing") is rewritten by close from this change's design.md.
- `add-inspect-skill` (refined) builds on this: a schema entry for `inspection` and its template.
